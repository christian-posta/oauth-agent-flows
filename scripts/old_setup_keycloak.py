"""
Keycloak setup script to configure the realm and clients.
"""
import os
import time
import httpx
import json
import argparse
from typing import Dict, Any

KEYCLOAK_URL = "http://localhost:8081"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
REALM_NAME = "ai-agents"

def log_message(message: str):
    """Log a message."""
    print(message)

async def wait_for_keycloak():
    """Wait for Keycloak to be ready."""
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{KEYCLOAK_URL}/health")
                if response.status_code == 200:
                    log_message("Keycloak is ready!")
                    break
        except Exception as e:
            log_message(f"Waiting for Keycloak to be ready... (Error: {str(e)})")
        time.sleep(5)

async def verify_realm_exists(token: str) -> bool:
    """Verify that the realm exists."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code == 200:
                log_message(f"Realm {REALM_NAME} exists and is accessible")
                return True
            else:
                log_message(f"Realm {REALM_NAME} does not exist or is not accessible")
                return False
        except Exception as e:
            log_message(f"Error verifying realm: {str(e)}")
            return False

async def get_admin_token() -> str:
    """Get admin access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
            },
        )
        response.raise_for_status()
        return response.json()["access_token"]

async def create_realm(token: str):
    """Create the AI agents realm."""
    realm_config = {
        "realm": REALM_NAME,
        "enabled": True,
        "displayName": "AI Agents Realm",
        "displayNameHtml": "<div class=\"kc-logo-text\"><span>AI Agents</span></div>",
        "registrationAllowed": False,
        "resetPasswordAllowed": True,
        "rememberMe": True,
        "loginWithEmailAllowed": True,
        "duplicateEmailsAllowed": False,
        "ssoSessionIdleTimeout": 1800,
        "ssoSessionMaxLifespan": 36000,
        "ssoSessionIdleTimeoutRememberMe": 1800,
        "ssoSessionMaxLifespanRememberMe": 36000,
        "offlineSessionIdleTimeout": 2592000,
        "offlineSessionMaxLifespanEnabled": False,
        "offlineSessionMaxLifespan": 5184000,
        "accessTokenLifespan": 300,
        "accessTokenLifespanForImplicitFlow": 900,
        "accessCodeLifespan": 60,
        "accessCodeLifespanUserAction": 300,
        "accessCodeLifespanLogin": 1800,
        "actionTokenGeneratedByUserLifespan": 300,
        "actionTokenGeneratedByAdminLifespan": 43200,
        "oauth2DeviceCodeLifespan": 300,
        "oauth2DevicePollingInterval": 5,
        "revokeRefreshToken": False,
        "refreshTokenMaxReuse": 0,
        "attributes": {
            "token-exchange-enabled": "true",
            "token.exchange": "true",
            "token-exchange-permission": "true"
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            # First try to get the realm to see if it exists
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}",
                headers={"Authorization": f"Bearer {token}"},
            )
            
            if response.status_code == 200:
                log_message(f"Realm {REALM_NAME} already exists, updating configuration...")
                # Update existing realm
                response = await client.put(
                    f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}",
                    json=realm_config,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                log_message(f"Updated realm {REALM_NAME} configuration")
            else:
                # Create new realm
                response = await client.post(
                    f"{KEYCLOAK_URL}/admin/realms",
                    json=realm_config,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                log_message(f"Created realm {REALM_NAME}")
        except httpx.HTTPStatusError as e:
            log_message(f"Error response from Keycloak: {e.response.text}")
            raise
        except Exception as e:
            log_message(f"Unexpected error: {str(e)}")
            raise

async def create_client(token: str, client_config: Dict[str, Any]):
    """Create a client in the realm."""
    # Enable authorization and service accounts for all service clients
    if client_config["clientId"] in ["agent-planner", "agent-tax-optimizer", "agent-calculator"]:
        client_config["authorizationServicesEnabled"] = True
        client_config["serviceAccountsEnabled"] = True
        client_config["authorizationSettings"] = {
            "allowRemoteResourceManagement": True,
            "policyEnforcementMode": "ENFORCING"
        }
        # Enable token exchange for service clients
        client_config["attributes"] = {
            "token-exchange-enabled": "true",
            "token.exchange": "true",
            "token-exchange-permission": "true"
        }
        log_message(f"Configuring client {client_config['clientId']} with settings: {json.dumps(client_config, indent=2)}")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients",
            json=client_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            log_message(f"Client {client_config['clientId']} already exists")
            # Update existing client to ensure authorization is enabled
            if client_config["clientId"] in ["agent-planner", "agent-tax-optimizer", "agent-calculator"]:
                # Get client ID
                response = await client.get(
                    f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients",
                    params={"clientId": client_config["clientId"]},
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                client_id = response.json()[0]["id"]
                
                # Update client
                response = await client.put(
                    f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_id}",
                    json=client_config,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
                log_message(f"Updated client {client_config['clientId']} with authorization enabled")
        else:
            response.raise_for_status()
            log_message(f"Created client {client_config['clientId']}")

async def create_client_scope(token: str, scope_config: Dict[str, Any]):
    """Create a client scope in the realm."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/client-scopes",
            json=scope_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            log_message(f"Client scope {scope_config['name']} already exists")
        else:
            response.raise_for_status()
            log_message(f"Created client scope {scope_config['name']}")

async def create_user(token: str, user_config: Dict[str, Any]):
    """Create a user in the realm."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users",
            json=user_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            log_message(f"User {user_config['username']} already exists")
        else:
            response.raise_for_status()
            log_message(f"Created user {user_config['username']}")

async def create_authorization_resource(token: str, client_id: str, resource_config: Dict[str, Any]):
    """Create an authorization resource for a client."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_id}/authz/resource-server/resource",
            json=resource_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            log_message(f"Resource {resource_config['name']} already exists for client {client_id}")
        else:
            response.raise_for_status()
            log_message(f"Created resource {resource_config['name']} for client {client_id}")

async def create_authorization_policy(token: str, client_id: str, policy_config: Dict[str, Any]):
    """Create an authorization policy for a client."""
    async with httpx.AsyncClient() as client:
        try:
            # First check if policy exists
            response = await client.get(
                f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_id}/authz/resource-server/policy",
                params={"name": policy_config["name"]},
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            policies = response.json()
            
            if any(p["name"] == policy_config["name"] for p in policies):
                log_message(f"Policy {policy_config['name']} already exists for client {client_id}")
                return

            # Create new policy with exact format required by Keycloak's ClientPolicyProviderFactory
            policy_data = {
                "name": policy_config["name"],
                "type": policy_config["type"],
                "logic": policy_config["logic"],
                "decisionStrategy": policy_config["decisionStrategy"],
                "config": {
                    "clients": policy_config["config"]["clients"]  # This is a JSON array string
                }
            }

            log_message(f"Creating policy with data: {policy_data}")
            response = await client.post(
                f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_id}/authz/resource-server/policy",
                json=policy_data,
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            log_message(f"Created policy {policy_config['name']} for client {client_id}")
        except httpx.HTTPStatusError as e:
            log_message(f"Error response from Keycloak: {e.response.text}")
            log_message(f"Request data: {policy_data}")
            raise
        except Exception as e:
            log_message(f"Unexpected error: {str(e)}")
            raise

async def create_authorization_permission(token: str, client_id: str, permission_config: Dict[str, Any]):
    """Create an authorization permission for a client."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_id}/authz/resource-server/permission",
            json=permission_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 409:
            log_message(f"Permission {permission_config['name']} already exists for client {client_id}")
        else:
            response.raise_for_status()
            log_message(f"Created permission {permission_config['name']} for client {client_id}")

async def setup_token_exchange(token: str, source_client: str, target_client: str):
    """Set up token exchange between two clients."""
    # Get client IDs
    async with httpx.AsyncClient() as client:
        # Get source client ID
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients",
            params={"clientId": source_client},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        source_client_id = response.json()[0]["id"]

        # Get target client ID
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients",
            params={"clientId": target_client},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        target_client_id = response.json()[0]["id"]

    # Create resource for token exchange
    resource_config = {
        "name": "Token Exchange Resource",
        "type": "urn:ietf:params:oauth:token-type:access_token",
        "uri": "/realms/ai-agents/protocol/openid-connect/token",
        "scopes": ["tax:process"]
    }
    await create_authorization_resource(token, target_client_id, resource_config)

    # Create policy to allow token exchange
    policy_config = {
        "name": f"Allow {source_client} token exchange",
        "type": "client",
        "logic": "POSITIVE",
        "decisionStrategy": "UNANIMOUS",
        "config": {
            "clients": json.dumps([source_client_id])
        }
    }
    await create_authorization_policy(token, target_client_id, policy_config)

    # Create permission
    permission_config = {
        "name": "Token Exchange Permission",
        "type": "resource",
        "logic": "POSITIVE",
        "decisionStrategy": "UNANIMOUS",
        "resources": ["Token Exchange Resource"],
        "policies": [f"Allow {source_client} token exchange"],
        "scopes": ["tax:process"]
    }
    await create_authorization_permission(token, target_client_id, permission_config)

    # Enable token exchange for both clients
    async with httpx.AsyncClient() as client:
        # Enable for source client
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{source_client_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        source_client_config = response.json()
        source_client_config["attributes"]["token.exchange"] = "true"
        source_client_config["attributes"]["token-exchange-enabled"] = "true"
        source_client_config["attributes"]["token-exchange-permission"] = "true"
        
        response = await client.put(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{source_client_id}",
            json=source_client_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()

        # Enable for target client
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{target_client_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        target_client_config = response.json()
        target_client_config["attributes"]["token.exchange"] = "true"
        target_client_config["attributes"]["token-exchange-enabled"] = "true"
        target_client_config["attributes"]["token-exchange-permission"] = "true"
        
        response = await client.put(
            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{target_client_id}",
            json=target_client_config,
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()

async def main():
    """Main setup function."""
    # Wait for Keycloak to be ready
    await wait_for_keycloak()

    # Get admin token
    token = await get_admin_token()

    # Verify realm exists
    if not await verify_realm_exists(token):
        log_message(f"Creating realm {REALM_NAME}...")
        await create_realm(token)
    else:
        log_message(f"Realm {REALM_NAME} already exists, updating configuration...")
        await create_realm(token)

    # Load realm configuration
    with open("keycloak/import/realm-export.json", "r") as f:
        realm_config = json.load(f)

    # Create client scopes
    for scope in realm_config["clientScopes"]:
        await create_client_scope(token, scope)

    # Create clients
    for client in realm_config["clients"]:
        await create_client(token, client)

    # Create users
    for user in realm_config["users"]:
        await create_user(token, user)

    # Set up token exchange permissions
    await setup_token_exchange(token, "agent-planner", "agent-tax-optimizer")
    await setup_token_exchange(token, "agent-planner", "agent-calculator")

    print("Keycloak setup completed successfully")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 