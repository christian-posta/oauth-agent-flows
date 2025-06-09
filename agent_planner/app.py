from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import os
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel
import logging
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Planner Service")
security = HTTPBearer()

# Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL")
REALM = os.getenv("REALM")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
PORT = int(os.getenv("PORT", "8001"))
TAX_OPTIMIZER_URL = os.getenv("TAX_OPTIMIZER_URL")

logger.info(f"Agent Planner Configuration:")
logger.info(f"KEYCLOAK_URL: {KEYCLOAK_URL}")
logger.info(f"REALM: {REALM}")
logger.info(f"CLIENT_ID: {CLIENT_ID}")
logger.info(f"TAX_OPTIMIZER_URL: {TAX_OPTIMIZER_URL}")

class FinancialData(BaseModel):
    income: float
    expenses: float
    savings: float
    investments: float

async def exchange_token(subject_token: str) -> dict:
    """Exchange the user's token for a token to call agent_tax_optimizer."""
    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    
    # Prepare the token exchange request
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": subject_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "audience": "agent-tax-optimizer",
        "scope": "tax:process",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    
    logger.info("Attempting token exchange with Keycloak")
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

@app.post("/test-token-exchange")
async def test_token_exchange(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Test token exchange functionality."""
    try:
        token = credentials.credentials
        logger.info("Testing token exchange...")
        
        # Just try the exchange without calling the other service
        token_response = await exchange_token(token)
        
        return {
            "status": "success",
            "message": "Token exchange successful",
            "token_type": token_response.get("token_type"),
            "expires_in": token_response.get("expires_in"),
            "scope": token_response.get("scope")
        }
    except Exception as e:
        logger.error(f"Test token exchange failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/generate-plan")
async def generate_plan(data: FinancialData, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Generate a financial plan based on the user's token."""
    try:
        # Get the token from the Authorization header
        token = credentials.credentials
        logger.info(f"Received token: {token[:20]}...")  # Log first 20 chars for security
        
        # Decode and verify the token
        try:
            decoded_token = jwt.get_unverified_claims(token)
            logger.info("Successfully decoded token")
        except Exception as e:
            logger.error(f"Failed to decode token: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid token format: {str(e)}")
        
        # Log the decoded token
        logger.info("Agent Planner received token:")
        logger.info(f"Decoded token: {decoded_token}")
        logger.info(f"Financial data: {data.dict()}")
        
        try:
            # Exchange the token for agent_tax_optimizer
            token_exchange_response = await exchange_token(token)
            logger.info("Token exchange completed")
        except Exception as e:
            logger.error(f"Token exchange failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")
        
        # Call agent_tax_optimizer with the new token
        tax_optimizer_url = f"{TAX_OPTIMIZER_URL}/optimize"
        logger.info(f"Calling tax optimizer at: {tax_optimizer_url}")
        logger.info(f"Using token: {token_exchange_response['access_token'][:20]}...")  # Log first 20 chars
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    tax_optimizer_url,
                    headers={"Authorization": f"Bearer {token_exchange_response['access_token']}"},
                    json=data.dict()  # Send the financial data
                )
                logger.info(f"Tax optimizer response status: {response.status_code}")
                logger.info(f"Tax optimizer response headers: {response.headers}")
                response.raise_for_status()
                tax_optimizer_response = response.json()
                logger.info("Tax optimizer response received:")
                logger.info(f"Response: {tax_optimizer_response}")
            except httpx.HTTPError as e:
                logger.error(f"Error calling tax optimizer: {e}")
                if hasattr(e, 'response'):
                    logger.error(f"Response status: {e.response.status_code}")
                    logger.error(f"Response headers: {e.response.headers}")
                    logger.error(f"Response body: {e.response.text}")
                raise HTTPException(status_code=500, detail=f"Failed to call tax optimizer: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error calling tax optimizer: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Unexpected error calling tax optimizer: {str(e)}")
        
        # Return a response with the token flow information
        response_data = {
            "message": "Financial plan generated successfully",
            "token_flow": {
                "original_token": {
                    "decoded": decoded_token,
                    "message": "Token received from user"
                },
                "token_exchange": {
                    "request": {
                        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                        "audience": "agent-tax-optimizer",
                        "scope": "tax:process"
                    },
                    "response": token_exchange_response,
                    "decoded_token": jwt.get_unverified_claims(token_exchange_response.get("access_token", "")) if token_exchange_response.get("access_token") else {},
                    "message": "Exchanged for agent_tax_optimizer token"
                },
                "agent_tax_optimizer": {
                    "original_token": {
                        "decoded": tax_optimizer_response.get("original_token", {}).get("decoded", {}),
                        "message": tax_optimizer_response.get("original_token", {}).get("message", "Token received by tax optimizer")
                    },
                    "token_exchange": {
                        "request": {
                            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                            "audience": "agent-calculator",
                            "scope": "calculator:process"
                        },
                        "response": tax_optimizer_response.get("token_exchange", {}),
                        "decoded_token": jwt.get_unverified_claims(tax_optimizer_response.get("token_exchange", {}).get("access_token", "")) if tax_optimizer_response.get("token_exchange", {}).get("access_token") else {},
                        "message": "Exchanged for agent_calculator token"
                    },
                    "calculator_response": {
                        "message": "Received response from calculator",
                        "tax_result": tax_optimizer_response.get("calculator_response", {}).get("tax_result", {})
                    },
                    "response": tax_optimizer_response,
                    "message": tax_optimizer_response.get("message", "Called agent_tax_optimizer successfully")
                }
            },
            "optimization_result": tax_optimizer_response.get("response", {}).get("optimization_result", {})
        }
        logger.info("Sending final response:")
        logger.info(f"Response data: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in generate_plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")

if __name__ == "__main__":
    logger.info(f"Agent Planner app initialized") 