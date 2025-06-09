#!/usr/bin/env python3

"""
Simple Keycloak debug script to test connection and basic operations.
"""

import requests
import json
import sys


def test_keycloak_connection(url, admin_user="admin", admin_pass="admin"):
    """Test Keycloak connection and basic operations."""
    
    print(f"Testing Keycloak connection to: {url}")
    
    # Test 1: Check if Keycloak is accessible - try multiple paths
    well_known_paths = [
        "/realms/master/.well-known/openid_configuration",
        "/auth/realms/master/.well-known/openid_configuration"
    ]
    
    keycloak_accessible = False
    working_base_path = ""
    
    for path in well_known_paths:
        try:
            test_url = f"{url}{path}"
            print(f"Trying: {test_url}")
            response = requests.get(test_url)
            if response.status_code == 200:
                print("✅ Keycloak is accessible")
                keycloak_accessible = True
                # Extract base path for admin API
                if "/auth/" in path:
                    working_base_path = "/auth"
                break
            else:
                print(f"   Status: {response.status_code}")
        except Exception as e:
            print(f"   Error: {e}")
    
    if not keycloak_accessible:
        print("❌ Keycloak well-known endpoint not found at any standard path")
        print("   Trying direct admin endpoint...")
        try:
            response = requests.get(f"{url}/admin/")
            if response.status_code == 200:
                print("✅ Keycloak admin endpoint accessible")
                keycloak_accessible = True
            else:
                print(f"❌ Admin endpoint not accessible. Status: {response.status_code}")
        except Exception as e:
            print(f"❌ Cannot reach admin endpoint: {e}")
            
    if not keycloak_accessible:
        return False
    
    # Test 2: Get admin token - try both paths
    admin_token_paths = [
        "/realms/master/protocol/openid-connect/token",
        "/auth/realms/master/protocol/openid-connect/token"
    ]
    
    admin_token = None
    working_token_path = ""
    
    for token_path in admin_token_paths:
        try:
            token_url = f"{url}{token_path}"
            print(f"Trying admin token at: {token_url}")
            response = requests.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": admin_user,
                    "password": admin_pass
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                admin_token = token_data.get('access_token')
                working_token_path = token_path
                print("✅ Admin authentication successful")
                break
            else:
                print(f"   Status: {response.status_code}")
                if response.status_code == 401:
                    print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    if not admin_token:
        print("❌ Admin authentication failed at all endpoints")
        return False
    
    # Test 3: Check existing realms - try both admin paths
    admin_api_paths = [
        "/admin/realms",
        "/auth/admin/realms"  
    ]
    
    realms_found = False
    working_admin_path = ""
    
    for admin_path in admin_api_paths:
        try:
            admin_url = f"{url}{admin_path}"
            print(f"Trying admin API at: {admin_url}")
            headers = {"Authorization": f"Bearer {admin_token}"}
            response = requests.get(admin_url, headers=headers)
            
            if response.status_code == 200:
                realms = response.json()
                working_admin_path = admin_path
                print(f"✅ Can access admin API. Found {len(realms)} realms:")
                for realm in realms:
                    print(f"  - {realm['realm']} ({'enabled' if realm['enabled'] else 'disabled'})")
                realms_found = True
                break
            else:
                print(f"   Status: {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    if not realms_found:
        print("❌ Cannot access admin API at any endpoint")
        return False
    
    # Test 4: Try to create a test realm
    test_realm_name = "test-debug-realm"
    try:
        # Check if test realm exists
        response = requests.get(f"{url}{working_admin_path.replace('/realms', '')}/realms/{test_realm_name}", headers=headers)
        if response.status_code == 200:
            print(f"ℹ️  Test realm {test_realm_name} already exists")
            # Delete it first
            delete_response = requests.delete(f"{url}{working_admin_path.replace('/realms', '')}/realms/{test_realm_name}", headers=headers)
            if delete_response.status_code == 204:
                print(f"✅ Deleted existing test realm")
            else:
                print(f"⚠️  Could not delete existing test realm: {delete_response.status_code}")
        
        # Create test realm with minimal config
        realm_data = {
            "realm": test_realm_name,
            "enabled": True
        }
        
        admin_base_url = f"{url}{working_admin_path.replace('/realms', '')}"
        create_url = f"{admin_base_url}/realms"
        print(f"Creating test realm at: {create_url}")
        
        response = requests.post(
            create_url,
            json=realm_data,
            headers=headers
        )
        
        if response.status_code == 201:
            print(f"✅ Test realm creation successful")
            
            # Clean up - delete the test realm
            delete_response = requests.delete(f"{admin_base_url}/realms/{test_realm_name}", headers=headers)
            if delete_response.status_code == 204:
                print(f"✅ Test realm cleanup successful")
            else:
                print(f"⚠️  Test realm cleanup failed: {delete_response.status_code}")
                
        else:
            print(f"❌ Test realm creation failed. Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Realm creation test error: {e}")
        return False
    
    # Print summary of working endpoints
    print(f"\n📋 Working endpoints for your Keycloak:")
    print(f"   Admin API: {url}{working_admin_path.replace('/realms', '')}")
    print(f"   Token endpoint: {url}{working_token_path}")
    
    print("🎉 All tests passed! Keycloak is working correctly.")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python debug_keycloak.py <keycloak_url> [admin_user] [admin_pass]")
        print("Example: python debug_keycloak.py http://localhost:8081")
        sys.exit(1)
    
    url = sys.argv[1].rstrip('/')
    admin_user = sys.argv[2] if len(sys.argv) > 2 else "admin"
    admin_pass = sys.argv[3] if len(sys.argv) > 3 else "admin"
    
    success = test_keycloak_connection(url, admin_user, admin_pass)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()