from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel
import logging
import json
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Tax Optimizer Service")
security = HTTPBearer()

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
REALM = os.getenv("REALM")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PORT = int(os.getenv("PORT", "8002"))
CALCULATOR_URL = os.getenv("CALCULATOR_URL")

logger.info(f"Agent Tax Optimizer Configuration:")
logger.info(f"KEYCLOAK_URL: {KEYCLOAK_URL}")
logger.info(f"REALM: {REALM}")
logger.info(f"CLIENT_ID: {CLIENT_ID}")
logger.info(f"PORT: {PORT}")
logger.info(f"CALCULATOR_URL: {CALCULATOR_URL}")

class FinancialData(BaseModel):
    income: float
    expenses: float
    savings: float
    investments: float

async def get_public_key() -> bytes:
    """Fetch the public key from Keycloak's JWKS endpoint."""
    jwks_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
    
    logger.info("Fetching JWKS from Keycloak")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks = response.json()
            
            # Log the available keys
            logger.info(f"Available keys in JWKS: {json.dumps(jwks, indent=2)}")
            
            # Find the signing key
            signing_key = None
            for key in jwks['keys']:
                if key.get('use') == 'sig' and key.get('alg') == 'RS256':
                    signing_key = key
                    break
            
            if not signing_key:
                raise Exception("No suitable signing key found in JWKS")
            
            logger.info(f"Using signing key with kid: {signing_key.get('kid')}")
            
            # Convert JWK to PEM format
            numbers = RSAPublicNumbers(
                e=int.from_bytes(base64.urlsafe_b64decode(signing_key['e'] + '==='), 'big'),
                n=int.from_bytes(base64.urlsafe_b64decode(signing_key['n'] + '==='), 'big')
            )
            public_key = numbers.public_key(backend=default_backend())
            pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return pem
            
        except Exception as e:
            logger.error(f"Error fetching JWKS: {str(e)}")
            raise

async def verify_token(token: str) -> dict:
    """Verify the JWT token with proper validation."""
    try:
        # First try to decode without verification to help with debugging
        try:
            unverified_token = jwt.get_unverified_claims(token)
            logger.info("Unverified token claims (for debugging):")
            logger.info(json.dumps(unverified_token, indent=2))
            
            # Log the key ID from the token header
            token_header = jwt.get_unverified_header(token)
            logger.info(f"Token header: {json.dumps(token_header, indent=2)}")
            
        except Exception as e:
            logger.error(f"Failed to decode token even without verification: {str(e)}")
        
        # Get the public key
        public_key = await get_public_key()
        
        # Log the expected issuer for debugging
        expected_issuer = f"{KEYCLOAK_URL}/realms/{REALM}"
        logger.info(f"Expected issuer: {expected_issuer}")
        logger.info(f"Actual issuer from token: {unverified_token.get('iss')}")
        
        # Now verify and decode the token
        decoded_token = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            audience=CLIENT_ID,  # Verify the token was intended for this service
            issuer=expected_issuer  # Verify the token was issued by our Keycloak
        )
        
        # Additional validation
        if 'scope' not in decoded_token or 'tax:process' not in decoded_token['scope']:
            logger.error(f"Token missing required scope. Token claims: {json.dumps(decoded_token, indent=2)}")
            raise HTTPException(
                status_code=403,
                detail="Token does not have required scope: tax:process"
            )
            
        return decoded_token
        
    except JWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        # Log the full error details
        logger.error(f"Full error details: {repr(e)}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error verifying token: {str(e)}")

@app.post("/optimize")
async def optimize_tax(data: FinancialData, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optimize tax based on the received token."""
    try:
        # Get the token from the Authorization header
        token = credentials.credentials
        logger.info(f"Received token: {token[:20]}...")  # Log first 20 chars for security
        
        # Verify the token
        decoded_token = await verify_token(token)
        logger.info("Successfully verified token")
        
        # Log the decoded token and financial data
        logger.info("Agent Tax Optimizer received token:")
        logger.info(f"Decoded token: {decoded_token}")
        logger.info(f"Financial data: {data.dict()}")
        
        # Exchange token for calculator service
        try:
            calculator_token_response = await exchange_token_for_calculator(token)
            logger.info("Token exchange for calculator completed")
        except Exception as e:
            logger.error(f"Token exchange for calculator failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Token exchange for calculator failed: {str(e)}")
        
        # Call calculator service
        calculator_url = f"{CALCULATOR_URL}/api/calculate"
        logger.info(f"Calling calculator at: {calculator_url}")
        logger.info(f"Using token: {calculator_token_response['access_token'][:20]}...")  # Log first 20 chars
        
        async with httpx.AsyncClient() as client:
            try:
                calculator_response = await client.post(
                    calculator_url,
                    headers={"Authorization": f"Bearer {calculator_token_response['access_token']}"}
                )
                logger.info(f"Calculator response status: {calculator_response.status_code}")
                logger.info(f"Calculator response headers: {calculator_response.headers}")
                calculator_response.raise_for_status()
                calculator_result = calculator_response.json()
                logger.info("Calculator response received:")
                logger.info(f"Response: {calculator_result}")
            except httpx.HTTPError as e:
                logger.error(f"Error calling calculator: {e}")
                if hasattr(e, 'response'):
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response headers: {e.response.headers}")
                    logger.error(f"Response body: {e.response.text}")
                raise HTTPException(status_code=500, detail=f"Failed to call calculator: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error calling calculator: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Unexpected error calling calculator: {str(e)}")
        
        # Calculate optimization results based on calculator results and financial data
        tax_result = calculator_result.get("tax_result", {})
        estimated_savings = min(data.income * 0.1, 5000)  # Example: 10% of income up to $5000
        recommendations = [
            "Maximize 401(k) contributions",
            "Consider tax-loss harvesting",
            "Review itemized deductions"
        ]
        
        # Return a response with token info and optimization results
        response = {
            "message": "Tax optimization completed",
            "original_token": {
                "decoded": decoded_token,
                "message": "Token received from agent_planner"
            },
            "token_exchange": {
                "request": {
                    "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                    "audience": "agent-calculator",
                    "scope": "tax:calculate"
                },
                "response": calculator_token_response,
                "decoded_token": jwt.get_unverified_claims(calculator_token_response.get("access_token", "")) if calculator_token_response.get("access_token") else {},
                "message": "Exchanged token for calculator service"
            },
            "calculator_response": {
                "message": "Received response from calculator",
                "tax_result": calculator_result.get("tax_result", {})
            },
            "response": {
                "message": "Tax optimization completed",
                "optimization_result": {
                    "estimated_savings": estimated_savings,
                    "recommendations": recommendations,
                    "calculator_result": tax_result
                }
            },
            "message": "Tax optimization completed"
        }
        logger.info("Sending response:")
        logger.info(f"Response data: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in optimize_tax: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error optimizing tax: {str(e)}")

async def exchange_token_for_calculator(subject_token: str) -> dict:
    """Exchange the user's token for a token to call agent_calculator."""
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    # Prepare the token exchange request
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": subject_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": "agent-calculator",
        "scope": "tax:calculate",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    logger.info("Attempting token exchange with Keycloak for calculator service")
    logger.info(f"Token exchange URL: {token_url}")
    # Don't log the actual secret, just confirm it's present
    log_data = data.copy()
    log_data["client_secret"] = "***REDACTED***" if CLIENT_SECRET else "MISSING"
    log_data["subject_token"] = f"{subject_token[:20]}...{subject_token[-10:]}" if subject_token else "MISSING"
    logger.info(f"Token exchange request data: {log_data}")
    
    async with httpx.AsyncClient() as client:
        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            response = await client.post(token_url, data=data, headers=headers)
            logger.info(f"Token exchange response status: {response.status_code}")
            logger.info(f"Token exchange response headers: {response.headers}")
            
            # Always log the response body for debugging
            response_text = response.text
            logger.info(f"Token exchange response body: {response_text}")
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed with status {response.status_code}")
                logger.error(f"Error response: {response_text}")
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"Token exchange failed: {response_text}"
                )
            
            token_response = response.json()
            logger.info("Token exchange successful")
            return token_response
            
        except httpx.HTTPError as e:
            logger.error(f"Token exchange HTTP error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {e.response.headers}")
                logger.error(f"Response body: {e.response.text}")
            raise HTTPException(status_code=500, detail=f"Failed to exchange token: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error during token exchange: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Agent Tax Optimizer app initialized") 