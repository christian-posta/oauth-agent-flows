import os
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
import uvicorn
from shared.keycloak_client import KeycloakClient

app = FastAPI()

# Configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]
REALM = os.environ["REALM"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

keycloak = KeycloakClient(KEYCLOAK_URL, REALM, CLIENT_ID, CLIENT_SECRET)

@app.post("/api/calculate-tax")
async def calculate_tax(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization[7:]
    
    try:
        # Validate token (should have tax:calculate scope)
        token_data = keycloak.validate_token(token)
        if "tax:calculate" not in token_data.get("scope", "").split():
            raise HTTPException(status_code=403, detail="Missing required scope: tax:calculate")
        
        # Extract user info from token
        user_id = token_data.get("sub", "unknown")
        
        # Perform fake tax calculation
        # In a real system, this would use the user's financial data
        calculated_tax = 5000.00
        
        return {
            "calculated_tax": calculated_tax,
            "message": "Tax calculated successfully",
            "user_id": user_id,
            "token_validated": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004) 