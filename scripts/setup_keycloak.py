#!/usr/bin/env python3

"""
Keycloak Token Exchange Setup Script

This script automates the complete setup for Standard Token Exchange in Keycloak 26.2.5
using configuration from a JSON file.

Usage:
    python setup_keycloak.py --config config.json --url http://localhost:8081
    
Requirements:
    pip install requests
"""

import argparse
import json
import sys
import time
from typing import Dict, List, Optional, Any
import requests
from urllib.parse import urljoin


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color


class KeycloakSetup:
    """Keycloak setup automation class."""
    
    def __init__(self, keycloak_url: str, admin_username: str = "admin", admin_password: str = "admin"):
        self.keycloak_url = keycloak_url.rstrip('/')
        self.admin_username = admin_username
        self.admin_password = admin_password
        self.admin_token = None
        self.session = requests.Session()
        self.debug = False
        self.admin_base_url = None  # Will be detected during setup
        
    def log(self, level: str, message: str):
        """Log messages with color coding."""
        colors = {
            'INFO': Colors.BLUE,
            'SUCCESS': Colors.GREEN,
            'WARNING': Colors.YELLOW,
            'ERROR': Colors.RED,
            'DEBUG': Colors.PURPLE
        }
        color = colors.get(level, Colors.WHITE)
        
        # Only print DEBUG messages if debug is enabled
        if level == 'DEBUG' and not self.debug:
            return
            
        print(f"{color}[{level}]{Colors.NC} {message}")
        
    def get_admin_token(self) -> bool:
        """Get admin access token."""
        self.log('INFO', 'Getting admin access token...')
        
        # Try multiple token endpoint paths
        token_paths = [
            "/realms/master/protocol/openid-connect/token",
            "/auth/realms/master/protocol/openid-connect/token"
        ]
        
        for token_path in token_paths:
            try:
                token_url = f"{self.keycloak_url}{token_path}"
                if self.debug:
                    self.log('DEBUG', f'Trying token endpoint: {token_url}')
                    
                response = self.session.post(
                    token_url,
                    data={
                        "grant_type": "password",
                        "client_id": "admin-cli",
                        "username": self.admin_username,
                        "password": self.admin_password
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.admin_token = token_data.get('access_token')
                    
                    if not self.admin_token:
                        continue
                        
                    self.session.headers.update({'Authorization': f'Bearer {self.admin_token}'})
                    self.log('SUCCESS', 'Admin token obtained')
                    if self.debug:
                        self.log('DEBUG', f'Working token endpoint: {token_url}')
                    return True
                elif self.debug:
                    self.log('DEBUG', f'Token endpoint failed with status: {response.status_code}')
                    
            except requests.exceptions.RequestException as e:
                if self.debug:
                    self.log('DEBUG', f'Token endpoint error: {e}')
                continue
        
        self.log('ERROR', 'Failed to get admin token from any endpoint')
        return False
        
    def detect_admin_base_url(self) -> bool:
        """Detect the correct admin API base URL."""
        admin_paths = ["/admin", "/auth/admin"]
        
        for admin_path in admin_paths:
            try:
                test_url = f"{self.keycloak_url}{admin_path}/realms"
                if self.debug:
                    self.log('DEBUG', f'Testing admin API at: {test_url}')
                    
                response = self.session.get(test_url)
                if response.status_code == 200:
                    self.admin_base_url = f"{self.keycloak_url}{admin_path}"
                    if self.debug:
                        self.log('DEBUG', f'Admin API base URL: {self.admin_base_url}')
                    return True
                elif self.debug:
                    self.log('DEBUG', f'Admin API test failed with status: {response.status_code}')
                    
            except requests.exceptions.RequestException as e:
                if self.debug:
                    self.log('DEBUG', f'Admin API test error: {e}')
                continue
        
        self.log('ERROR', 'Could not detect admin API base URL')
        return False
            
    def create_realm(self, realm_config: Dict[str, Any]) -> bool:
        """Create a realm."""
        realm_name = realm_config['name']
        self.log('INFO', f'Creating realm: {realm_name}...')
        
        if not self.admin_base_url:
            if not self.detect_admin_base_url():
                return False
        
        try:
            # Check if realm exists
            response = self.session.get(f"{self.admin_base_url}/realms/{realm_name}")
            if response.status_code == 200:
                self.log('WARNING', f'Realm {realm_name} already exists, skipping creation')
                return True
                
            # Create realm - use proper Keycloak realm structure
            realm_data = {
                "realm": realm_config['name'],
                "displayName": realm_config.get('displayName', realm_config['name']),
                "enabled": realm_config.get('enabled', True)
            }
            
            # Add optional settings only if they're reasonable values
            if 'accessTokenLifespan' in realm_config:
                realm_data["accessTokenLifespan"] = realm_config['accessTokenLifespan']
            if 'accessTokenLifespanForImplicitFlow' in realm_config:
                realm_data["accessTokenLifespanForImplicitFlow"] = realm_config['accessTokenLifespanForImplicitFlow']
            if 'ssoSessionIdleTimeout' in realm_config:
                realm_data["ssoSessionIdleTimeout"] = realm_config['ssoSessionIdleTimeout']
            if 'ssoSessionMaxLifespan' in realm_config:
                realm_data["ssoSessionMaxLifespan"] = realm_config['ssoSessionMaxLifespan']
            if 'offlineSessionIdleTimeout' in realm_config:
                realm_data["offlineSessionIdleTimeout"] = realm_config['offlineSessionIdleTimeout']
            
            if self.debug:
                self.log('DEBUG', f'Realm data: {json.dumps(realm_data, indent=2)}')
            
            response = self.session.post(
                f"{self.admin_base_url}/realms",
                json=realm_data
            )
            
            if response.status_code != 201:
                self.log('ERROR', f'Failed to create realm. Status: {response.status_code}')
                self.log('ERROR', f'Response: {response.text}')
                return False
            
            self.log('SUCCESS', f'Realm {realm_name} created')
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to create realm {realm_name}: {e}')
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    self.log('ERROR', f'Error details: {error_detail}')
                except:
                    self.log('ERROR', f'Error response: {e.response.text}')
            return False
            
    def create_client_scope(self, realm_name: str, scope_config: Dict[str, Any]) -> bool:
        """Create a client scope."""
        scope_name = scope_config['name']
        self.log('INFO', f'Creating client scope: {scope_name}...')
        
        try:
            # Check if scope exists
            response = self.session.get(f"{self.admin_base_url}/realms/{realm_name}/client-scopes")
            response.raise_for_status()
            
            existing_scopes = response.json()
            if any(scope['name'] == scope_name for scope in existing_scopes):
                self.log('WARNING', f'Client scope {scope_name} already exists, skipping creation')
                return True
                
            # Create scope
            response = self.session.post(
                f"{self.admin_base_url}/realms/{realm_name}/client-scopes",
                json=scope_config
            )
            response.raise_for_status()
            
            self.log('SUCCESS', f'Client scope {scope_name} created')
            
            # Add mappers if specified
            if 'mappers' in scope_config and scope_config['mappers']:
                scope_id = self.get_client_scope_id(realm_name, scope_name)
                if scope_id:
                    for mapper in scope_config['mappers']:
                        self.add_scope_mapper(realm_name, scope_id, mapper)
                        
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to create client scope {scope_name}: {e}')
            return False
            
    def get_client_scope_id(self, realm_name: str, scope_name: str) -> Optional[str]:
        """Get client scope UUID by name."""
        try:
            response = self.session.get(f"{self.admin_base_url}/realms/{realm_name}/client-scopes")
            response.raise_for_status()
            
            scopes = response.json()
            for scope in scopes:
                if scope['name'] == scope_name:
                    return scope['id']
                    
            return None
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to get client scope ID for {scope_name}: {e}')
            return None
            
    def add_scope_mapper(self, realm_name: str, scope_id: str, mapper_config: Dict[str, Any]) -> bool:
        """Add a mapper to a client scope."""
        mapper_name = mapper_config['name']
        self.log('INFO', f'Adding mapper {mapper_name} to scope...')
        
        try:
            # Check if mapper exists
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/client-scopes/{scope_id}/protocol-mappers/models"
            )
            response.raise_for_status()
            
            existing_mappers = response.json()
            if any(mapper['name'] == mapper_name for mapper in existing_mappers):
                self.log('WARNING', f'Mapper {mapper_name} already exists, skipping creation')
                return True
                
            # Create mapper
            mapper_data = {
                "name": mapper_name,
                "protocol": "openid-connect",
                "protocolMapper": mapper_config['type'],
                "config": mapper_config['config']
            }
            
            response = self.session.post(
                f"{self.admin_base_url}/realms/{realm_name}/client-scopes/{scope_id}/protocol-mappers/models",
                json=mapper_data
            )
            response.raise_for_status()
            
            self.log('SUCCESS', f'Mapper {mapper_name} added')
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to add mapper {mapper_name}: {e}')
            return False
            
    def create_client(self, realm_name: str, client_config: Dict[str, Any]) -> bool:
        """Create a client."""
        client_id = client_config['clientId']
        self.log('INFO', f'Creating client: {client_id}...')
        
        try:
            # Check if client exists
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/clients",
                params={"clientId": client_id}
            )
            response.raise_for_status()
            
            existing_clients = response.json()
            if existing_clients:
                self.log('WARNING', f'Client {client_id} already exists, updating token exchange settings...')
                # Update existing client with token exchange settings
                client_uuid = existing_clients[0]['id']
                return self.update_client_token_exchange(realm_name, client_uuid, client_config)
                
            # Prepare client configuration
            client_data = {
                "clientId": client_id,
                "name": client_config.get('name', client_id),
                "enabled": client_config.get('enabled', True),
                "protocol": "openid-connect"
            }
            
            # Configure based on client type
            if client_config['type'] == 'public':
                client_data.update({
                    "publicClient": True,
                    "standardFlowEnabled": client_config.get('standardFlowEnabled', True),
                    "directAccessGrantsEnabled": client_config.get('directAccessGrantsEnabled', True),
                    "redirectUris": client_config.get('redirectUris', []),
                    "webOrigins": client_config.get('webOrigins', [])
                })
            else:  # confidential
                client_data.update({
                    "publicClient": False,
                    "serviceAccountsEnabled": client_config.get('serviceAccountsEnabled', True),
                    "standardFlowEnabled": client_config.get('standardFlowEnabled', False),
                    "directAccessGrantsEnabled": client_config.get('directAccessGrantsEnabled', False)
                })
                
                # Add token exchange settings for confidential clients
                if client_config.get('tokenExchange', {}).get('enabled', False):
                    if "attributes" not in client_data:
                        client_data["attributes"] = {}
                    client_data["attributes"]["token.exchange.standard.enabled"] = "true"
                    
                    refresh_setting = client_config.get('tokenExchange', {}).get('allowRefreshToken')
                    if refresh_setting:
                        client_data["attributes"]["token.exchange.refresh.enabled"] = refresh_setting
                        
            if self.debug:
                self.log('DEBUG', f'Client data: {json.dumps(client_data, indent=2)}')
                        
            # Create client
            response = self.session.post(
                f"{self.admin_base_url}/realms/{realm_name}/clients",
                json=client_data
            )
            response.raise_for_status()
            
            self.log('SUCCESS', f'Client {client_id} created')
            
            # Create client roles if specified
            if 'roles' in client_config:
                for role in client_config['roles']:
                    self.create_client_role(realm_name, client_id, role)
                    
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to create client {client_id}: {e}')
            return False
            
    def update_client_token_exchange(self, realm_name: str, client_uuid: str, client_config: Dict[str, Any]) -> bool:
        """Update client with token exchange settings."""
        client_id = client_config['clientId']
        self.log('INFO', f'Updating token exchange settings for client {client_id}...')
        
        try:
            # Get current client configuration
            response = self.session.get(f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}")
            response.raise_for_status()
            current_client = response.json()
            
            # Update attributes for token exchange
            if client_config.get('tokenExchange', {}).get('enabled', False):
                if "attributes" not in current_client:
                    current_client["attributes"] = {}
                current_client["attributes"]["token.exchange.standard.enabled"] = "true"
                
                refresh_setting = client_config.get('tokenExchange', {}).get('allowRefreshToken')
                if refresh_setting:
                    current_client["attributes"]["token.exchange.refresh.enabled"] = refresh_setting
                    
                if self.debug:
                    self.log('DEBUG', f'Updated client attributes: {current_client.get("attributes", {})}')
                    
                # Update the client
                response = self.session.put(
                    f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}",
                    json=current_client
                )
                response.raise_for_status()
                
                self.log('SUCCESS', f'Token exchange enabled for client {client_id}')
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to update token exchange for client {client_id}: {e}')
            return False
            
    def get_client_uuid(self, realm_name: str, client_id: str) -> Optional[str]:
        """Get client UUID by client ID."""
        try:
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/clients",
                params={"clientId": client_id}
            )
            response.raise_for_status()
            
            clients = response.json()
            if clients:
                return clients[0]['id']
                
            return None
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to get client UUID for {client_id}: {e}')
            return None
            
    def create_client_role(self, realm_name: str, client_id: str, role_config: Dict[str, Any]) -> bool:
        """Create a client role."""
        role_name = role_config['name']
        self.log('INFO', f'Creating role {role_name} in client {client_id}...')
        
        try:
            client_uuid = self.get_client_uuid(realm_name, client_id)
            if not client_uuid:
                self.log('ERROR', f'Client {client_id} not found')
                return False
                
            # Check if role exists
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}/roles/{role_name}"
            )
            if response.status_code == 200:
                self.log('WARNING', f'Role {role_name} already exists in client {client_id}, skipping creation')
                return True
                
            # Create role
            role_data = {
                "name": role_name,
                "description": role_config.get('description', '')
            }
            
            response = self.session.post(
                f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}/roles",
                json=role_data
            )
            response.raise_for_status()
            
            self.log('SUCCESS', f'Role {role_name} created in client {client_id}')
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to create role {role_name} in client {client_id}: {e}')
            return False
            
    def assign_client_scope(self, realm_name: str, client_id: str, scope_name: str, assignment_type: str = 'default') -> bool:
        """Assign a client scope to a client."""
        self.log('INFO', f'Assigning scope {scope_name} to client {client_id} as {assignment_type}...')
        
        try:
            client_uuid = self.get_client_uuid(realm_name, client_id)
            scope_uuid = self.get_client_scope_id(realm_name, scope_name)
            
            if not client_uuid:
                self.log('ERROR', f'Client {client_id} not found')
                return False
                
            if not scope_uuid:
                self.log('ERROR', f'Client scope {scope_name} not found')
                return False
                
            # Check if scope is already assigned
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}/{assignment_type}-client-scopes"
            )
            response.raise_for_status()
            
            assigned_scopes = response.json()
            if any(scope['name'] == scope_name for scope in assigned_scopes):
                self.log('WARNING', f'Scope {scope_name} already assigned to client {client_id} as {assignment_type}, skipping')
                return True
                
            # Assign scope
            response = self.session.put(
                f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}/{assignment_type}-client-scopes/{scope_uuid}"
            )
            response.raise_for_status()
            
            self.log('SUCCESS', f'Scope {scope_name} assigned to client {client_id} as {assignment_type}')
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to assign scope {scope_name} to client {client_id}: {e}')
            return False
            
    def create_user(self, realm_name: str, user_config: Dict[str, Any]) -> bool:
        """Create a user."""
        username = user_config['username']
        self.log('INFO', f'Creating user: {username}...')
        
        try:
            # Check if user exists
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/users",
                params={"username": username}
            )
            response.raise_for_status()
            
            existing_users = response.json()
            if existing_users:
                self.log('WARNING', f'User {username} already exists, skipping creation')
                return True
                
            # Create user
            user_data = {
                "username": username,
                "email": user_config.get('email'),
                "firstName": user_config.get('firstName'),
                "lastName": user_config.get('lastName'),
                "enabled": user_config.get('enabled', True),
                "emailVerified": user_config.get('emailVerified', True)
            }
            
            if 'password' in user_config:
                user_data["credentials"] = [{
                    "type": "password",
                    "value": user_config['password'],
                    "temporary": user_config.get('temporary', False)
                }]
                
            response = self.session.post(
                f"{self.admin_base_url}/realms/{realm_name}/users",
                json=user_data
            )
            response.raise_for_status()
            
            self.log('SUCCESS', f'User {username} created')
            
            # Assign client roles if specified
            if 'clientRoles' in user_config:
                for client_id, roles in user_config['clientRoles'].items():
                    for role_name in roles:
                        self.assign_client_role_to_user(realm_name, username, client_id, role_name)
                        
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to create user {username}: {e}')
            return False
            
    def get_user_uuid(self, realm_name: str, username: str) -> Optional[str]:
        """Get user UUID by username."""
        try:
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/users",
                params={"username": username}
            )
            response.raise_for_status()
            
            users = response.json()
            if users:
                return users[0]['id']
                
            return None
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to get user UUID for {username}: {e}')
            return None
            
    def assign_client_role_to_user(self, realm_name: str, username: str, client_id: str, role_name: str) -> bool:
        """Assign a client role to a user."""
        self.log('INFO', f'Assigning role {role_name} from client {client_id} to user {username}...')
        
        try:
            user_uuid = self.get_user_uuid(realm_name, username)
            client_uuid = self.get_client_uuid(realm_name, client_id)
            
            if not user_uuid:
                self.log('ERROR', f'User {username} not found')
                return False
                
            if not client_uuid:
                self.log('ERROR', f'Client {client_id} not found')
                return False
                
            # Get role details
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}/roles/{role_name}"
            )
            response.raise_for_status()
            role_data = response.json()
            
            # Assign role
            response = self.session.post(
                f"{self.admin_base_url}/realms/{realm_name}/users/{user_uuid}/role-mappings/clients/{client_uuid}",
                json=[role_data]
            )
            response.raise_for_status()
            
            self.log('SUCCESS', f'Role {role_name} from client {client_id} assigned to user {username}')
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to assign role {role_name} from client {client_id} to user {username}: {e}')
            return False
            
    def get_client_secret(self, realm_name: str, client_id: str) -> Optional[str]:
        """Get client secret."""
        try:
            client_uuid = self.get_client_uuid(realm_name, client_id)
            if not client_uuid:
                return None
                
            response = self.session.get(
                f"{self.admin_base_url}/realms/{realm_name}/clients/{client_uuid}/client-secret"
            )
            response.raise_for_status()
            
            secret_data = response.json()
            return secret_data.get('value')
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Failed to get client secret for {client_id}: {e}')
            return None
            
    def test_token_exchange(self, realm_name: str, config: Dict[str, Any]) -> bool:
        """Test token exchange functionality."""
        self.log('INFO', 'Testing token exchange functionality...')
        
        try:
            # Get user token
            user_token_response = self.session.post(
                f"{self.keycloak_url}/realms/{realm_name}/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": "user-web-app",
                    "username": "testuser",
                    "password": "password123",
                    "scope": "openid"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            user_token_response.raise_for_status()
            user_token = user_token_response.json()['access_token']
            
            # Get agent-planner client secret
            planner_secret = self.get_client_secret(realm_name, "agent-planner")
            if not planner_secret:
                self.log('ERROR', 'Could not get agent-planner client secret')
                return False
                
            # Test token exchange
            exchange_response = self.session.post(
                f"{self.keycloak_url}/realms/{realm_name}/protocol/openid-connect/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "client_id": "agent-planner",
                    "client_secret": planner_secret,
                    "subject_token": user_token,
                    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "audience": "agent-tax-optimizer"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            exchange_response.raise_for_status()
            
            exchanged_token = exchange_response.json()
            self.log('SUCCESS', 'Token exchange test successful!')
            self.log('INFO', f'Exchanged token type: {exchanged_token.get("token_type")}')
            self.log('INFO', f'Expires in: {exchanged_token.get("expires_in")} seconds')
            
            return True
            
        except requests.exceptions.RequestException as e:
            self.log('ERROR', f'Token exchange test failed: {e}')
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    self.log('ERROR', f'Error details: {error_detail}')
                except:
                    self.log('ERROR', f'Error response: {e.response.text}')
            return False
            
    def setup_from_config(self, config: Dict[str, Any]) -> bool:
        """Set up Keycloak from configuration."""
        self.log('INFO', 'Starting Keycloak setup from configuration...')
        
        # Detect admin base URL first
        if not self.detect_admin_base_url():
            return False
        
        realm_name = config['realm']['name']
        
        # Step 1: Create realm
        if not self.create_realm(config['realm']):
            return False
            
        # Step 2: Create client scopes
        self.log('INFO', 'Creating client scopes...')
        for scope in config.get('clientScopes', []):
            if not self.create_client_scope(realm_name, scope):
                return False
                
        # Step 3: Create clients
        self.log('INFO', 'Creating clients...')
        for client in config.get('clients', []):
            if not self.create_client(realm_name, client):
                return False
                
        # Step 4: Assign client scopes to clients
        self.log('INFO', 'Assigning client scopes to clients...')
        for client in config.get('clients', []):
            client_id = client['clientId']
            
            # Assign default scopes
            for scope_name in client.get('assignedScopes', {}).get('default', []):
                if not self.assign_client_scope(realm_name, client_id, scope_name, 'default'):
                    self.log('WARNING', f'Failed to assign default scope {scope_name} to client {client_id}')
                    
            # Assign optional scopes  
            for scope_name in client.get('assignedScopes', {}).get('optional', []):
                if not self.assign_client_scope(realm_name, client_id, scope_name, 'optional'):
                    self.log('WARNING', f'Failed to assign optional scope {scope_name} to client {client_id}')
                    
        # Step 5: Create users
        self.log('INFO', 'Creating users...')
        for user in config.get('users', []):
            if not self.create_user(realm_name, user):
                return False
                
        self.log('SUCCESS', 'Keycloak setup completed successfully!')
        return True
        
    def print_summary(self, config: Dict[str, Any]) -> None:
        """Print setup summary."""
        realm_name = config['realm']['name']
        
        print(f"\n{Colors.CYAN}=== KEYCLOAK SETUP SUMMARY ==={Colors.NC}")
        print(f"Keycloak URL: {self.keycloak_url}")
        print(f"Realm: {realm_name}")
        
        print(f"\n{Colors.WHITE}Clients:{Colors.NC}")
        for client in config.get('clients', []):
            client_id = client['clientId']
            client_type = client['type']
            token_exchange = client.get('tokenExchange', {}).get('enabled', False)
            
            print(f"  • {client_id} ({client_type})")
            if token_exchange:
                print(f"    - Token exchange: ✅ enabled")
            if client['type'] == 'confidential':
                secret = self.get_client_secret(realm_name, client_id)
                if secret:
                    print(f"    - Client secret: {secret}")
                    
        print(f"\n{Colors.WHITE}Client Scopes:{Colors.NC}")
        for scope in config.get('clientScopes', []):
            print(f"  • {scope['name']}: {scope['description']}")
            
        print(f"\n{Colors.WHITE}Users:{Colors.NC}")
        for user in config.get('users', []):
            print(f"  • {user['username']} ({user['email']})")
            if 'clientRoles' in user:
                for client_id, roles in user['clientRoles'].items():
                    print(f"    - {client_id}: {', '.join(roles)}")
                    
        print(f"\n{Colors.WHITE}Token Exchange Rules:{Colors.NC}")
        for rule in config.get('tokenExchangeRules', []):
            print(f"  • {rule['description']}")
            print(f"    - Requester: {rule['requesterClient']}")
            print(f"    - Targets: {', '.join(rule['targetClients'])}")
            print(f"    - Scopes: {', '.join(rule['allowedScopes'])}")
            
        print(f"\n{Colors.GREEN}🎉 Setup complete! You can now test token exchange.{Colors.NC}")
        
    def print_test_commands(self, config: Dict[str, Any]) -> None:
        """Print test commands."""
        realm_name = config['realm']['name']
        planner_secret = self.get_client_secret(realm_name, "agent-planner")
        
        print(f"\n{Colors.CYAN}=== TEST COMMANDS ==={Colors.NC}")
        
        print(f"\n{Colors.WHITE}1. Get user token:{Colors.NC}")
        print(f"""curl -X POST \\
  {self.keycloak_url}/realms/{realm_name}/protocol/openid-connect/token \\
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'grant_type=password' \\
  -d 'client_id=user-web-app' \\
  -d 'username=testuser' \\
  -d 'password=password123' \\
  -d 'scope=openid'""")
        
        print(f"\n{Colors.WHITE}2. Exchange token (basic):{Colors.NC}")
        print(f"""curl -X POST \\
  {self.keycloak_url}/realms/{realm_name}/protocol/openid-connect/token \\
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange' \\
  -d 'client_id=agent-planner' \\
  -d 'client_secret={planner_secret}' \\
  -d 'subject_token=USER_ACCESS_TOKEN' \\
  -d 'subject_token_type=urn:ietf:params:oauth:token-type:access_token' \\
  -d 'requested_token_type=urn:ietf:params:oauth:token-type:access_token' \\
  -d 'audience=agent-tax-optimizer'""")
        
        print(f"\n{Colors.WHITE}3. Exchange token (with scope):{Colors.NC}")
        print(f"""curl -X POST \\
  {self.keycloak_url}/realms/{realm_name}/protocol/openid-connect/token \\
  -H 'Content-Type: application/x-www-form-urlencoded' \\
  -d 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange' \\
  -d 'client_id=agent-planner' \\
  -d 'client_secret={planner_secret}' \\
  -d 'subject_token=USER_ACCESS_TOKEN' \\
  -d 'subject_token_type=urn:ietf:params:oauth:token-type:access_token' \\
  -d 'requested_token_type=urn:ietf:params:oauth:token-type:access_token' \\
  -d 'audience=agent-tax-optimizer' \\
  -d 'scope=tax:process'""")


def load_config(config_file: str) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Colors.RED}[ERROR]{Colors.NC} Configuration file {config_file} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{Colors.RED}[ERROR]{Colors.NC} Invalid JSON in configuration file: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Keycloak Token Exchange Setup Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup_keycloak.py --config config.json --url http://localhost:8081
  python setup_keycloak.py --config config.json --url http://localhost:8081 --test
  python setup_keycloak.py --config config.json --url http://localhost:8081 --admin-user admin --admin-pass mypassword
        """
    )
    
    parser.add_argument('--config', '-c', required=True, help='Path to configuration JSON file')
    parser.add_argument('--url', '-u', default='http://localhost:8080', help='Keycloak URL (default: http://localhost:8080)')
    parser.add_argument('--admin-user', default='admin', help='Admin username (default: admin)')
    parser.add_argument('--admin-pass', default='admin', help='Admin password (default: admin)')
    parser.add_argument('--test', action='store_true', help='Run token exchange test after setup')
    parser.add_argument('--summary', action='store_true', help='Print setup summary')
    parser.add_argument('--test-commands', action='store_true', help='Print test commands')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize Keycloak setup
    setup = KeycloakSetup(args.url, args.admin_user, args.admin_pass)
    
    # Enable debug logging if requested
    if args.debug:
        setup.debug = True
    
    # Get admin token
    if not setup.get_admin_token():
        print(f"{Colors.RED}[ERROR]{Colors.NC} Failed to authenticate with Keycloak")
        print(f"Check that Keycloak is running at {args.url} and credentials are correct")
        sys.exit(1)
        
    # Run setup
    if not setup.setup_from_config(config):
        print(f"{Colors.RED}[ERROR]{Colors.NC} Setup failed")
        sys.exit(1)
        
    # Print summary
    if args.summary or args.verbose:
        setup.print_summary(config)
        
    # Print test commands
    if args.test_commands or args.verbose:
        setup.print_test_commands(config)
        
    # Run test
    if args.test:
        print(f"\n{Colors.CYAN}=== RUNNING TOKEN EXCHANGE TEST ==={Colors.NC}")
        if setup.test_token_exchange(config['realm']['name'], config):
            print(f"{Colors.GREEN}✅ Token exchange test passed!{Colors.NC}")
        else:
            print(f"{Colors.RED}❌ Token exchange test failed!{Colors.NC}")
            sys.exit(1)


if __name__ == '__main__':
    main()