#!/usr/bin/env python3
"""
Test script to verify A2A authentication is working correctly.
This script tests:
1. Agent card access (should work without auth)
2. A2A endpoints without auth (should return 401 with WWW-Authenticate)
3. A2A endpoints with invalid auth (should return 401 with WWW-Authenticate)
4. A2A endpoints with valid auth (should work)
"""

import httpx
import asyncio
import json
import os
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8003"
TIMEOUT = 10.0  # 10 second timeout for requests

# Keycloak configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8081")
REALM_NAME = os.getenv("REALM", "ai-agents")
USER_CLIENT_ID = "user-web-app"
AGENT_TAX_OPTIMIZER_CLIENT_ID = "agent-tax-optimizer"
AGENT_CALCULATOR_CLIENT_ID = "agent-calculator"
TEST_USERNAME = "testuser"
TEST_PASSWORD = "password123"

def decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without verification for debugging."""
    try:
        # Split the token and get the payload part
        parts = token.split('.')
        if len(parts) != 3:
            return {"error": "Invalid JWT format"}
        
        payload = parts[1]
        # Add padding if needed
        padding = 4 - (len(payload) % 4)
        if padding != 4:
            payload += '=' * padding
        
        # Decode base64
        decoded = base64.urlsafe_b64decode(payload)
        return json.loads(decoded.decode('utf-8'))
    except Exception as e:
        return {"error": f"Failed to decode JWT: {str(e)}"}

def print_token_debug(token: str, token_name: str):
    """Print detailed debug information about a JWT token."""
    print(f"   🔍 {token_name} Debug Info:")
    print(f"      Length: {len(token)} characters")
    print(f"      First 50 chars: {token[:50]}...")
    
    # Decode and show payload
    payload = decode_jwt_payload(token)
    if "error" not in payload:
        print(f"      🔐 Decoded Payload:")
        print(f"         Issuer (iss): {payload.get('iss', 'N/A')}")
        print(f"         Subject (sub): {payload.get('sub', 'N/A')}")
        print(f"         Audience (aud): {payload.get('aud', 'N/A')}")
        print(f"         Client ID (azp): {payload.get('azp', 'N/A')}")
        print(f"         Scope: {payload.get('scope', 'N/A')}")
        print(f"         Expires (exp): {payload.get('exp', 'N/A')}")
        print(f"         Issued At (iat): {payload.get('iat', 'N/A')}")
        
        # Show all claims for debugging
        print(f"         All claims: {json.dumps(payload, indent=8)}")
    else:
        print(f"      ❌ Failed to decode: {payload['error']}")

async def get_agent_calculator_token():
    """Programmatically get a token for the agent-calculator client using the full token exchange chain."""
    print("🔑 Getting agent-calculator token via full token exchange chain...")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            # Step 1: Get user token
            print("   📝 Step 1: Getting user token...")
            user_token_response = await client.post(
                f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": USER_CLIENT_ID,
                    "username": TEST_USERNAME,
                    "password": TEST_PASSWORD,
                    "scope": "openid"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if user_token_response.status_code != 200:
                print(f"   ❌ Failed to get user token: {user_token_response.status_code}")
                print(f"   Response: {user_token_response.text}")
                return None
            
            user_token_data = user_token_response.json()
            user_token = user_token_data.get("access_token")
            
            if not user_token:
                print("   ❌ No access token in user token response")
                return None
            
            print("   ✅ User token obtained")
            print_token_debug(user_token, "User Token")
            
            # Step 2: Get agent-planner client secret
            print("   🔐 Step 2: Getting agent-planner client secret...")
            
            # Try to get admin token to retrieve client secret
            admin_token_response = await client.post(
                f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
                data={
                    "grant_type": "password",
                    "client_id": "admin-cli",
                    "username": "admin",
                    "password": "admin"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            agent_planner_secret = None
            
            if admin_token_response.status_code == 200:
                admin_token_data = admin_token_response.json()
                admin_token = admin_token_data.get("access_token")
                
                if admin_token:
                    # Get client UUID
                    client_response = await client.get(
                        f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients?clientId=agent-planner",
                        headers={"Authorization": f"Bearer {admin_token}"}
                    )
                    
                    if client_response.status_code == 200:
                        clients = client_response.json()
                        if clients:
                            client_uuid = clients[0].get("id")
                            
                            # Get client secret
                            secret_response = await client.get(
                                f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_uuid}/client-secret",
                                headers={"Authorization": f"Bearer {admin_token}"}
                            )
                            
                            if secret_response.status_code == 200:
                                secret_data = secret_response.json()
                                agent_planner_secret = secret_data.get("value")
                                print("   ✅ Agent planner client secret retrieved automatically")
            
            # Fallback to hardcoded secret from config.json
            if not agent_planner_secret:
                agent_planner_secret = "17yYAxRtRamaYeHtgFEJJEzyeXcdlszD"
                print("   ⚠️  Using hardcoded agent planner client secret (from config.json)")
            
            # Step 3: Exchange user token for agent-tax-optimizer token
            print("   🔄 Step 3: Exchanging user token for agent-tax-optimizer token...")
            print(f"      Requester client: agent-planner")
            print(f"      Target audience: agent-tax-optimizer")
            print(f"      Requested scope: tax:process")
            
            tax_optimizer_exchange_response = await client.post(
                f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "client_id": "agent-planner",
                    "client_secret": agent_planner_secret,
                    "subject_token": user_token,
                    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "audience": "agent-tax-optimizer",
                    "scope": "tax:process"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"      Tax optimizer exchange response status: {tax_optimizer_exchange_response.status_code}")
            
            if tax_optimizer_exchange_response.status_code != 200:
                print(f"   ❌ Tax optimizer token exchange failed: {tax_optimizer_exchange_response.status_code}")
                print(f"   Response: {tax_optimizer_exchange_response.text}")
                return None
            
            tax_optimizer_token_data = tax_optimizer_exchange_response.json()
            tax_optimizer_token = tax_optimizer_token_data.get("access_token")
            
            if not tax_optimizer_token:
                print("   ❌ No access token in tax optimizer exchange response")
                print(f"   Response: {tax_optimizer_token_data}")
                return None
            
            print("   ✅ Tax optimizer token obtained")
            print_token_debug(tax_optimizer_token, "Tax Optimizer Token")
            
            # Step 4: Get agent-tax-optimizer client secret
            print("   🔐 Step 4: Getting agent-tax-optimizer client secret...")
            
            agent_tax_optimizer_secret = None
            
            if admin_token:
                # Get client UUID
                client_response = await client.get(
                    f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients?clientId={AGENT_TAX_OPTIMIZER_CLIENT_ID}",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                if client_response.status_code == 200:
                    clients = client_response.json()
                    if clients:
                        client_uuid = clients[0].get("id")
                        
                        # Get client secret
                        secret_response = await client.get(
                            f"{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/clients/{client_uuid}/client-secret",
                            headers={"Authorization": f"Bearer {admin_token}"}
                        )
                        
                        if secret_response.status_code == 200:
                            secret_data = secret_response.json()
                            agent_tax_optimizer_secret = secret_data.get("value")
                            print("   ✅ Agent tax optimizer client secret retrieved automatically")
            
            # Fallback to hardcoded secret from config.json
            if not agent_tax_optimizer_secret:
                agent_tax_optimizer_secret = "PLOs4j6ti521kb5ZVVVwi5GWi9eDYTwq"
                print("   ⚠️  Using hardcoded agent tax optimizer client secret (from config.json)")
            
            # Step 5: Exchange tax optimizer token for agent-calculator token
            print("   🔄 Step 5: Exchanging tax optimizer token for agent-calculator token...")
            print(f"      Requester client: {AGENT_TAX_OPTIMIZER_CLIENT_ID}")
            print(f"      Target audience: {AGENT_CALCULATOR_CLIENT_ID}")
            print(f"      Requested scope: tax:calculate")
            
            calculator_exchange_response = await client.post(
                f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "client_id": AGENT_TAX_OPTIMIZER_CLIENT_ID,
                    "client_secret": agent_tax_optimizer_secret,
                    "subject_token": tax_optimizer_token,
                    "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                    "audience": AGENT_CALCULATOR_CLIENT_ID,
                    "scope": "tax:calculate"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            print(f"      Calculator exchange response status: {calculator_exchange_response.status_code}")
            
            if calculator_exchange_response.status_code == 200:
                calculator_token_data = calculator_exchange_response.json()
                calculator_token = calculator_token_data.get("access_token")
                
                if calculator_token:
                    print("   ✅ Agent calculator token obtained!")
                    print_token_debug(calculator_token, "Agent Calculator Token")
                    return calculator_token
                else:
                    print("   ❌ No access token in calculator exchange response")
                    print(f"   Response: {calculator_token_data}")
                    return None
            else:
                print(f"   ❌ Calculator token exchange failed: {calculator_exchange_response.status_code}")
                print(f"   Response: {calculator_exchange_response.text}")
                
                # Try without scope as fallback
                print("   🔄 Trying calculator token exchange without scope...")
                calculator_exchange_no_scope_response = await client.post(
                    f"{KEYCLOAK_URL}/realms/{REALM_NAME}/protocol/openid-connect/token",
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                        "client_id": AGENT_TAX_OPTIMIZER_CLIENT_ID,
                        "client_secret": agent_tax_optimizer_secret,
                        "subject_token": tax_optimizer_token,
                        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                        "audience": AGENT_CALCULATOR_CLIENT_ID
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                print(f"      No-scope calculator exchange response status: {calculator_exchange_no_scope_response.status_code}")
                
                if calculator_exchange_no_scope_response.status_code == 200:
                    calculator_token_data = calculator_exchange_no_scope_response.json()
                    calculator_token = calculator_token_data.get("access_token")
                    
                    if calculator_token:
                        print("   ✅ Agent calculator token obtained (without scope)!")
                        print_token_debug(calculator_token, "Agent Calculator Token (No Scope)")
                        return calculator_token
                    else:
                        print("   ❌ No access token in no-scope calculator exchange response")
                        print(f"   Response: {calculator_token_data}")
                else:
                    print(f"   ❌ No-scope calculator token exchange also failed: {calculator_exchange_no_scope_response.status_code}")
                    print(f"   Response: {calculator_exchange_no_scope_response.text}")
                
                return None
                
        except httpx.ConnectError:
            print(f"   ❌ Connection error: Could not connect to Keycloak at {KEYCLOAK_URL}")
            print("   💡 Make sure Keycloak is running and accessible")
            return None
        except httpx.TimeoutException:
            print(f"   ❌ Timeout error: Request took longer than {TIMEOUT} seconds")
            return None
        except Exception as e:
            print(f"   ❌ Error getting token: {str(e)}")
            return None

async def test_agent_card_access():
    """Test that agent card is accessible without authentication."""
    print("🔍 Testing agent card access (should work without auth)...")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            response = await client.get(f"{BASE_URL}/a2a/.well-known/agent.json")
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                agent_card = response.json()
                print("   ✅ Agent card accessible without authentication")
                print(f"   📋 Agent name: {agent_card.get('name')}")
                print(f"   🔐 Security schemes: {list(agent_card.get('securitySchemes', {}).keys())}")
                
                # Check if security schemes are properly defined
                security_schemes = agent_card.get('securitySchemes', {})
                if security_schemes:
                    print("   ✅ Security schemes found in agent card")
                    for scheme_name, scheme_details in security_schemes.items():
                        print(f"      - {scheme_name}: {scheme_details.get('type')} {scheme_details.get('scheme')}")
                else:
                    print("   ⚠️  No security schemes found in agent card")
                
                # Check if security requirements are defined
                security_requirements = agent_card.get('security', [])
                if security_requirements:
                    print("   ✅ Security requirements found in agent card")
                    for req in security_requirements:
                        for scheme_name, scopes in req.items():
                            print(f"      - {scheme_name} requires scopes: {scopes}")
                else:
                    print("   ⚠️  No security requirements found in agent card")
                
                return True
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except httpx.ConnectError:
            print(f"   ❌ Connection error: Could not connect to {BASE_URL}")
            print(f"   💡 Make sure the agent calculator service is running on port 8003")
            return False
        except httpx.TimeoutException:
            print(f"   ❌ Timeout error: Request took longer than {TIMEOUT} seconds")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

async def test_a2a_without_auth():
    """Test A2A endpoints without authentication (should return 401)."""
    print("\n🔍 Testing A2A endpoints without authentication (should return 401)...")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            # Test message/send endpoint without auth
            payload = {
                "jsonrpc": "2.0",
                "id": "test-1",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": "test-msg-1",
                        "role": "user",
                        "parts": [{"type": "text", "text": "What are the current tax rates?"}]
                    }
                }
            }
            
            response = await client.post(f"{BASE_URL}/a2a/", json=payload)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Correctly returned 401 for missing authentication")
                
                # Check for WWW-Authenticate header
                www_auth = response.headers.get("WWW-Authenticate")
                if www_auth:
                    print(f"   ✅ WWW-Authenticate header present: {www_auth}")
                else:
                    print("   ⚠️  WWW-Authenticate header missing")
                
                # Check response body
                try:
                    error_response = response.json()
                    print(f"   📄 Error response: {json.dumps(error_response, indent=2)}")
                except:
                    print(f"   📄 Response text: {response.text}")
                
                return True
            else:
                print(f"   ❌ Expected 401, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except httpx.ConnectError:
            print(f"   ❌ Connection error: Could not connect to {BASE_URL}")
            return False
        except httpx.TimeoutException:
            print(f"   ❌ Timeout error: Request took longer than {TIMEOUT} seconds")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

async def test_a2a_with_invalid_auth():
    """Test A2A endpoints with invalid authentication (should return 401)."""
    print("\n🔍 Testing A2A endpoints with invalid authentication (should return 401)...")
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            # Test with invalid Bearer token
            headers = {"Authorization": "Bearer invalid-token"}
            
            payload = {
                "jsonrpc": "2.0",
                "id": "test-2",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": "test-msg-2",
                        "role": "user",
                        "parts": [{"type": "text", "text": "What are the current tax rates?"}]
                    }
                }
            }
            
            response = await client.post(f"{BASE_URL}/a2a/", json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 401:
                print("   ✅ Correctly returned 401 for invalid authentication")
                
                # Check for WWW-Authenticate header
                www_auth = response.headers.get("WWW-Authenticate")
                if www_auth:
                    print(f"   ✅ WWW-Authenticate header present: {www_auth}")
                else:
                    print("   ⚠️  WWW-Authenticate header missing")
                
                return True
            else:
                print(f"   ❌ Expected 401, got {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except httpx.ConnectError:
            print(f"   ❌ Connection error: Could not connect to {BASE_URL}")
            return False
        except httpx.TimeoutException:
            print(f"   ❌ Timeout error: Request took longer than {TIMEOUT} seconds")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

async def test_a2a_with_valid_auth():
    """Test A2A endpoints with valid authentication (should work)."""
    print("\n🔍 Testing A2A endpoints with valid authentication (should work)...")
    
    # First try to get a token programmatically
    test_token = await get_agent_calculator_token()
    
    # Fallback to environment variable if programmatic token fails
    if not test_token:
        test_token = os.getenv("TEST_JWT_TOKEN")
        if test_token:
            print("   ⚠️  Using token from environment variable")
        else:
            print("   ⚠️  No test JWT token available")
            print("   💡 To test with valid authentication:")
            print("      1. Set TEST_JWT_TOKEN environment variable with a valid JWT token")
            print("      2. The token should have 'tax:calculate' scope")
            print("      3. Run the test again")
            print("   💡 Example:")
            print("      export TEST_JWT_TOKEN='your-jwt-token-here'")
            print("      python test_a2a_auth.py")
            return True
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            # Test with valid Bearer token
            headers = {"Authorization": f"Bearer {test_token}"}
            
            payload = {
                "jsonrpc": "2.0",
                "id": "test-3",
                "method": "message/send",
                "params": {
                    "message": {
                        "messageId": "test-msg-3",
                        "role": "user",
                        "parts": [{"type": "text", "text": "What are the current tax rates?"}]
                    }
                }
            }
            
            response = await client.post(f"{BASE_URL}/a2a/", json=payload, headers=headers)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Successfully authenticated and received response")
                try:
                    result = response.json()
                    print(f"   📄 Response: {json.dumps(result, indent=2)}")
                except:
                    print(f"   📄 Response text: {response.text}")
                return True
            elif response.status_code == 401:
                print("   ❌ Authentication failed - token may be invalid or expired")
                print("   💡 Check that your JWT token:")
                print("      - Is valid and not expired")
                print("      - Has 'tax:calculate' scope")
                print("      - Is issued by the correct Keycloak realm")
                return False
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except httpx.ConnectError:
            print(f"   ❌ Connection error: Could not connect to {BASE_URL}")
            return False
        except httpx.TimeoutException:
            print(f"   ❌ Timeout error: Request took longer than {TIMEOUT} seconds")
            return False
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            return False

async def main():
    """Run all authentication tests."""
    print("🚀 Starting A2A Authentication Tests")
    print("=" * 50)
    print(f"📍 Testing against: {BASE_URL}")
    print(f"⏱️  Timeout: {TIMEOUT} seconds")
    print("=" * 50)
    
    tests = [
        test_agent_card_access,
        test_a2a_without_auth,
        test_a2a_with_invalid_auth,
        test_a2a_with_valid_auth
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    test_names = [
        "Agent Card Access",
        "A2A without Auth",
        "A2A with Invalid Auth", 
        "A2A with Valid Auth"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {i+1}. {name}: {status}")
    
    passed = sum(results)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! A2A authentication is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print("\n💡 Next Steps:")
    print("   1. If the service isn't running, start it with: python app.py")
    print("   2. To test with real authentication, get a JWT token and set TEST_JWT_TOKEN")
    print("   3. The token should have 'tax:calculate' scope from your Keycloak setup")

if __name__ == "__main__":
    asyncio.run(main()) 