#!/usr/bin/env python3

"""
Script to directly check and enable token exchange for agent-planner client
"""

import requests
import json
import sys

def fix_token_exchange(keycloak_url, admin_user="admin", admin_pass="admin"):
    """Fix token exchange for agent-planner client."""
    
    print("🔧 Fixing token exchange for agent-planner...")
    
    # Get admin token
    try:
        response = requests.post(
            f"{keycloak_url}/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": admin_user,
                "password": admin_pass
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        admin_token = response.json()['access_token']
        print("✅ Got admin token")
    except Exception as e:
        print(f"❌ Failed to get admin token: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Get agent-planner client
    try:
        response = requests.get(
            f"{keycloak_url}/admin/realms/ai-agents/clients",
            params={"clientId": "agent-planner"},
            headers=headers
        )
        response.raise_for_status()
        clients = response.json()
        
        if not clients:
            print("❌ agent-planner client not found")
            return False
            
        client = clients[0]
        client_uuid = client['id']
        print(f"✅ Found agent-planner client: {client_uuid}")
        
        # Show current settings
        print(f"📋 Current client settings:")
        print(f"   - publicClient: {client.get('publicClient', 'N/A')}")
        print(f"   - serviceAccountsEnabled: {client.get('serviceAccountsEnabled', 'N/A')}")
        print(f"   - attributes: {client.get('attributes', {})}")
        
    except Exception as e:
        print(f"❌ Failed to get client: {e}")
        return False
    
    # Update client with token exchange enabled
    try:
        # Ensure attributes exist
        if 'attributes' not in client:
            client['attributes'] = {}
            
        # Set token exchange attributes
        client['attributes']['token.exchange.standard.enabled'] = 'true'
        
        print(f"\n🔄 Updating client with:")
        print(f"   - token.exchange.standard.enabled: true")
        print(f"   - Full attributes: {client['attributes']}")
        
        # Update the client
        response = requests.put(
            f"{keycloak_url}/admin/realms/ai-agents/clients/{client_uuid}",
            json=client,
            headers=headers
        )
        response.raise_for_status()
        
        print("✅ Client updated successfully")
        
    except Exception as e:
        print(f"❌ Failed to update client: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False
    
    # Verify the update
    try:
        response = requests.get(
            f"{keycloak_url}/admin/realms/ai-agents/clients/{client_uuid}",
            headers=headers
        )
        response.raise_for_status()
        updated_client = response.json()
        
        print(f"\n✅ Verification:")
        print(f"   - token.exchange.standard.enabled: {updated_client.get('attributes', {}).get('token.exchange.standard.enabled', 'NOT SET')}")
        
        if updated_client.get('attributes', {}).get('token.exchange.standard.enabled') == 'true':
            print("🎉 Token exchange is now enabled!")
            return True
        else:
            print("❌ Token exchange still not enabled")
            return False
            
    except Exception as e:
        print(f"❌ Failed to verify update: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python fix_token_exchange.py <keycloak_url> [admin_user] [admin_pass]")
        print("Example: python fix_token_exchange.py http://localhost:8081")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    admin_user = sys.argv[2] if len(sys.argv) > 2 else "admin"
    admin_pass = sys.argv[3] if len(sys.argv) > 3 else "admin"
    
    success = fix_token_exchange(url, admin_user, admin_pass)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()