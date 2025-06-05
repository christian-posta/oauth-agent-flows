from fastapi import FastAPI, Header, HTTPException
import requests
import uvicorn
from shared.keycloak_client import KeycloakClient
import os
from dotenv import load_dotenv

app = FastAPI()

# Configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]
REALM = os.environ["REALM"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

keycloak = KeycloakClient(KEYCLOAK_URL, REALM, CLIENT_ID, CLIENT_SECRET)

@app.post("/api/plan")
async def create_plan(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization[7:]  # Remove "Bearer "
    
    try:
        # Validate the token
        keycloak.validate_token(token)
        
        # Exchange token for agent-tax-optimizer
        token_response = keycloak.exchange_token(
            subject_token=token,
            audience="agent-tax-optimizer",
            scope="tax:process"
        )
        new_token = token_response["access_token"]
        
        # Call agent-tax-optimizer with new token
        optimizer_response = requests.post(
            "http://localhost:8002/api/optimize",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        optimizer_response.raise_for_status()
        
        return {
            "message": "Planning completed",
            "optimization_result": optimizer_response.json()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 