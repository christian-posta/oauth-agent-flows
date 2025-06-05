import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import uvicorn
from shared.keycloak_client import KeycloakClient
import requests

app = FastAPI()

# Configuration
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

KEYCLOAK_URL = os.environ["KEYCLOAK_URL"]
REALM = os.environ["REALM"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REDIRECT_URI = os.environ["REDIRECT_URI"]

keycloak = KeycloakClient(KEYCLOAK_URL, REALM, CLIENT_ID, CLIENT_SECRET)

@app.get("/")
def home():
    return {"message": "User App - Click /login to start"}

@app.get("/login") 
def login():
    auth_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "financial:read tax:process",
        "redirect_uri": REDIRECT_URI
    }
    return RedirectResponse(url=f"{auth_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")

@app.get("/callback")
async def callback(code: str):
    try:
        # Exchange authorization code for token
        token_response = keycloak.exchange_authorization_code(code, REDIRECT_URI)
        access_token = token_response["access_token"]
        
        # Call agent-planner with the token
        planner_response = requests.post(
            "http://localhost:8001/api/plan",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        planner_response.raise_for_status()
        
        return {
            "message": "Success",
            "planning_result": planner_response.json()
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000) 