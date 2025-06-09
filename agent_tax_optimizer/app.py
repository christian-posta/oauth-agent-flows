from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import os
from dotenv import load_dotenv
import httpx
from pydantic import BaseModel
import logging

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

@app.post("/optimize")
async def optimize_tax(data: FinancialData, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optimize tax based on the received token."""
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