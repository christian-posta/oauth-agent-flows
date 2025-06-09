#!/usr/bin/env python3

"""
Script to debug token exchange settings and try different attribute names
"""

import requests
import json
import sys

def debug_token_exchange(keycloak_url, admin_user="admin", admin_pass="admin"):
    """Debug and fix token exchange settings."""
    
    print("🔍 Debugging token exchange settings...")
    
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
        
    except Exception as e:
        print(f"❌ Failed to get client: {e}")
        return False
    
    # Check different token exchange attribute combinations
    token_exchange_attrs = [
        'token.exchange.standard.enabled',
        'oauth2.token.exchange.grant.enabled', 
        'token-exchange-standard-enabled',
        'token.exchange.enabled'
    ]
    
    print(f"\n📋 Current client configuration:")
    print(f"   - clientId: {client.get('clientId')}")
    print(f"   - publicClient: {client.get('publicClient')}")
    print(f"   - serviceAccountsEnabled: {client.get('serviceAccountsEnabled')}")
    print(f"   - standardFlowEnabled: {client.get('standardFlowEnabled')}")
    print(f"   - directAccessGrantsEnabled: {client.get('directAccessGrantsEnabled')}")
    print(f"   - Full attributes: {json.dumps(client.get('attributes', {}), indent=4)}")
    
    # Try setting multiple possible attribute names
    print(f"\n🔧 Trying different token exchange attribute names...")
    
    for attr_name in token_exchange_attrs:
        try:
            if 'attributes' not in client:
                client['attributes'] = {}
                
            client['attributes'][attr_name] = 'true'
            print(f"   Setting {attr_name} = true")
            
        except Exception as e:
            print(f"   ❌ Failed to set {attr_name}: {e}")
    
    # Also try setting protocol mappers that might be needed
    client['attributes']['token.exchange.standard.enabled'] = 'true'
    
    # Update client
    try:
        print(f"\n🔄 Updating client with all token exchange attributes...")
        print(f"   Final attributes: {json.dumps(client.get('attributes', {}), indent=4)}")
        
        response = requests.put(
            f"{keycloak_url}/admin/realms/ai-agents/clients/{client_uuid}",
            json=client,
            headers=headers
        )
        response.raise_for_status()
        print("✅ Client updated")
        
    except Exception as e:
        print(f"❌ Failed to update client: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False
    
    # Test token exchange directly
    print(f"\n🧪 Testing token exchange directly...")
    
    try:
        # Get user token first
        user_response = requests.post(
            f"{keycloak_url}/realms/ai-agents/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "user-web-app",
                "username": "testuser",
                "password": "password123",
                "scope": "openid"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        user_response.raise_for_status()
        user_token = user_response.json()['access_token']
        print("✅ Got user token")
        
        # Get client secret
        secret_response = requests.get(
            f"{keycloak_url}/admin/realms/ai-agents/clients/{client_uuid}/client-secret",
            headers=headers
        )
        secret_response.raise_for_status()
        client_secret = secret_response.json()['value']
        print("✅ Got client secret")
        
        # Try token exchange
        exchange_response = requests.post(
            f"{keycloak_url}/realms/ai-agents/protocol/openid-connect/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "client_id": "agent-planner",
                "client_secret": client_secret,
                "subject_token": user_token,
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "audience": "agent-tax-optimizer"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if exchange_response.status_code == 200:
            print("🎉 Token exchange SUCCESS!")
            exchanged = exchange_response.json()
            print(f"   Got token: {exchanged.get('token_type')} (expires in {exchanged.get('expires_in')}s)")
            return True
        else:
            print(f"❌ Token exchange failed: {exchange_response.status_code}")
            try:
                error = exchange_response.json()
                print(f"   Error: {error.get('error')}: {error.get('error_description')}")
            except:
                print(f"   Raw response: {exchange_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Token exchange test failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_token_exchange.py <keycloak_url> [admin_user] [admin_pass]")
        print("Example: python debug_token_exchange.py http://localhost:8081")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    admin_user = sys.argv[2] if len(sys.argv) > 2 else "admin"
    admin_pass = sys.argv[3] if len(sys.argv) > 3 else "admin"
    
    success = debug_token_exchange(url, admin_user, admin_pass)
    
    if success:
        print("\n🎉 Token exchange is working!")
    else:
        print("\n❌ Token exchange still not working. Try manually enabling it in the UI:")
        print("   1. Go to Keycloak admin console")
        print("   2. Navigate to: Clients → agent-planner → Settings")
        print("   3. Scroll to 'Capability config' section") 
        print("   4. Enable 'Standard Token Exchange' toggle")
        print("   5. Click Save")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()