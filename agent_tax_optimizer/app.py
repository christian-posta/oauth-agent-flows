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

@app.post("/api/optimize")
async def optimize_taxes(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization[7:]
    
    try:
        # Validate token (should have tax:process scope)
        token_data = keycloak.validate_token(token)
        if "tax:process" not in token_data.get("scope", "").split():
            raise HTTPException(status_code=403, detail="Missing required scope: tax:process")
        
        # Exchange token for agent-calculator
        token_response = keycloak.exchange_token(
            subject_token=token,
            audience="agent-calculator",
            scope="tax:calculate"
        )
        new_token = token_response["access_token"]
        
        # Call agent-calculator with new token
        calculator_response = requests.post(
            "http://localhost:8003/api/calculate",
            headers={"Authorization": f"Bearer {new_token}"}
        )
        calculator_response.raise_for_status()
        
        return {
            "message": "Tax optimization completed",
            "calculation_result": calculator_response.json()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002) 