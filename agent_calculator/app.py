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

app = FastAPI(title="Agent Calculator Service")
security = HTTPBearer()

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
REALM = os.getenv("REALM")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PORT = int(os.getenv("PORT", "8003"))

logger.info(f"Agent Calculator Configuration:")
logger.info(f"KEYCLOAK_URL: {KEYCLOAK_URL}")
logger.info(f"REALM: {REALM}")
logger.info(f"CLIENT_ID: {CLIENT_ID}")
logger.info(f"PORT: {PORT}")

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
        if 'scope' not in decoded_token or 'tax:calculate' not in decoded_token['scope']:
            logger.error(f"Token missing required scope. Token claims: {json.dumps(decoded_token, indent=2)}")
            raise HTTPException(
                status_code=403,
                detail="Token does not have required scope: tax:calculate"
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

@app.post("/api/calculate")
async def calculate_tax(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Calculate tax based on the received token."""
    try:
        # Get the token from the Authorization header
        token = credentials.credentials
        logger.info(f"Received token: {token[:20]}...")  # Log first 20 chars for security
        
        # Verify the token
        decoded_token = await verify_token(token)
        logger.info("Successfully verified token")
        
        # Log the decoded token
        logger.info("Agent Calculator received token:")
        logger.info(f"Decoded token: {decoded_token}")
        
        # Simulate tax calculations
        # In a real implementation, this would use actual tax calculation logic
        tax_calculations = {
            "federal_tax_rate": 0.22,  # Example: 22% federal tax rate
            "state_tax_rate": 0.05,    # Example: 5% state tax rate
            "effective_tax_rate": 0.27, # Combined rate
            "tax_brackets": [
                {"min": 0, "max": 10000, "rate": 0.10},
                {"min": 10000, "max": 40000, "rate": 0.12},
                {"min": 40000, "max": 85000, "rate": 0.22},
                {"min": 85000, "max": 163300, "rate": 0.24},
                {"min": 163300, "max": 207350, "rate": 0.32},
                {"min": 207350, "max": 518400, "rate": 0.35},
                {"min": 518400, "max": None, "rate": 0.37}
            ],
            "deductions": {
                "standard_deduction": 12950,
                "itemized_deductions": {
                    "mortgage_interest": 0,
                    "property_tax": 0,
                    "charitable_contributions": 0
                }
            },
            "credits": {
                "child_tax_credit": 2000,
                "earned_income_credit": 0
            }
        }
        
        # Return the calculation results
        response = {
            "message": "Tax calculations completed",
            "tax_result": tax_calculations
        }
        logger.info("Sending response:")
        logger.info(f"Response data: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in calculate_tax: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating tax: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Agent Calculator app initialized")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT) 