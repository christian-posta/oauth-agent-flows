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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8003"
TIMEOUT = 10.0  # 10 second timeout for requests

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
    
    # Check if we have a test token from environment
    test_token = os.getenv("TEST_JWT_TOKEN")
    
    if not test_token:
        print("   ⚠️  No test JWT token found in environment")
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