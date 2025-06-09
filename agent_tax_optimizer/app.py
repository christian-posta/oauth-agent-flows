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

logger.info(f"Agent Tax Optimizer Configuration:")
logger.info(f"KEYCLOAK_URL: {KEYCLOAK_URL}")
logger.info(f"REALM: {REALM}")
logger.info(f"CLIENT_ID: {CLIENT_ID}")
logger.info(f"PORT: {PORT}")

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
        
        # Calculate some example optimization results based on the financial data
        estimated_savings = min(data.income * 0.1, 5000)  # Example: 10% of income up to $5000
        recommendations = [
            "Maximize 401(k) contributions",
            "Consider tax-loss harvesting",
            "Review itemized deductions"
        ]
        
        # Return a response with token info and optimization results
        response = {
            "message": "Tax optimization completed",
            "token_info": decoded_token,
            "optimization_result": {
                "estimated_savings": estimated_savings,
                "recommendations": recommendations
            }
        }
        logger.info("Sending response:")
        logger.info(f"Response data: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in optimize_tax: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error optimizing tax: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Agent Tax Optimizer app initialized") 