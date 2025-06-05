"""
User web application for the AI agent demo.
"""
import os
import sys
from pathlib import Path

# Add the services directory to the Python path
services_dir = str(Path(__file__).parent.parent)
if services_dir not in sys.path:
    sys.path.append(services_dir)

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import httpx
from jose import jwt
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from pydantic import BaseModel


# Load environment variables
load_dotenv()

app = FastAPI(title="AI Agent Demo - User Web App")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files only in production
if os.getenv("ENVIRONMENT", "development") == "production":
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# OAuth2 configuration
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="login",
    tokenUrl="token"
)

# Keycloak configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8081/auth")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "ai-agents")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "user-web-app")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")

# In-memory session storage (replace with proper session management in production)
sessions = {}

# Models
class FinancialData(BaseModel):
    income: float
    expenses: float
    savings: float
    investments: float

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    # In development, redirect to Vite dev server
    if os.getenv("ENVIRONMENT", "development") == "development":
        return RedirectResponse(url="http://localhost:5173")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/user")
async def get_user(request: Request):
    """Get current user information."""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

@app.get("/api/token")
async def get_token(request: Request):
    """Get current access token."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = sessions[session_id]
    return {"access_token": session["access_token"]}

@app.get("/api/delegation-info")
async def get_delegation_info(request: Request):
    """Get delegation chain information."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # In a real implementation, this would fetch the actual delegation chain
    return {
        "delegation_chain": [
            {
                "from": "user",
                "to": "financial_planner",
                "permissions": ["financial:read", "financial:write"]
            },
            {
                "from": "financial_planner",
                "to": "tax_optimizer",
                "permissions": ["tax:read", "tax:write"]
            }
        ]
    }

@app.post("/api/financial-planning")
async def create_financial_plan(data: FinancialData, request: Request):
    """Create a financial plan."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get the access token
    access_token = sessions[session_id]["access_token"]
    
    # TODO: Implement financial planning logic
    return {
        "status": "success",
        "message": "Financial plan created successfully",
        "data": data.dict()
    }

@app.get("/login")
async def login():
    """Redirect to Keycloak login page."""
    auth_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth"
    params = {
        "client_id": KEYCLOAK_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "openid profile email financial:read tax:process"
    }
    
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    full_url = f"{auth_url}?{query_string}"
    
    return RedirectResponse(url=full_url)

@app.get("/callback")
async def callback(request: Request, code: str = None, error: str = None, error_description: str = None):
    """Handle the OAuth2 callback from Keycloak."""
    if error:
        print(f"Keycloak error: {error} - {error_description}")
        raise HTTPException(status_code=400, detail=f"Authentication failed: {error_description}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No authorization code received")
        
    # Exchange the authorization code for tokens
    token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    print(f"Token URL: {token_url}")
    print(f"Request data: {data}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(token_url, data=data)
            print(f"Token response status: {response.status_code}")
            print(f"Token response body: {response.text}")
            response.raise_for_status()
            tokens = response.json()
        except httpx.HTTPError as e:
            print(f"Error exchanging code for token: {e}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise HTTPException(status_code=400, detail="Failed to get access token")
    
    # Get user info
    try:
        claims = jwt.get_unverified_claims(tokens['access_token'])
        issuer_url = claims['iss']
        userinfo_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/userinfo"
        
        headers = {
            "Authorization": f"Bearer {tokens['access_token']}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(userinfo_url, headers=headers)
                response.raise_for_status()
                user_info = response.json()
            except httpx.HTTPError as e:
                print(f"Error getting user info: {e}")
                raise HTTPException(status_code=400, detail="Failed to get user info")
    except Exception as e:
        print(f"Error getting token claims: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to get token claims")
    
    # Create session
    session_id = os.urandom(16).hex()
    sessions[session_id] = {
        "user_info": user_info,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "expires_at": datetime.now() + timedelta(seconds=tokens["expires_in"])
    }
    
    # Set session cookie and redirect to home
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=3600
    )
    return response

@app.post("/api/logout")
async def logout(request: Request):
    """Logout the user."""
    session_id = request.cookies.get("session_id")
    if session_id in sessions:
        del sessions[session_id]
    
    response = JSONResponse(content={"status": "success"})
    response.delete_cookie("session_id")
    return response

async def get_current_user(request: Request) -> Optional[dict]:
    """Get the current user from the session."""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None
    
    session = sessions[session_id]
    if datetime.now() > session["expires_at"]:
        # Token expired, try to refresh
        if "refresh_token" in session:
            try:
                token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
                data = {
                    "grant_type": "refresh_token",
                    "client_id": KEYCLOAK_CLIENT_ID,
                    "client_secret": KEYCLOAK_CLIENT_SECRET,
                    "refresh_token": session["refresh_token"]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(token_url, data=data)
                    if response.status_code == 200:
                        tokens = response.json()
                        session["access_token"] = tokens["access_token"]
                        session["refresh_token"] = tokens["refresh_token"]
                        session["expires_at"] = datetime.now() + timedelta(seconds=tokens["expires_in"])
                        return session["user_info"]
            except Exception:
                pass
        
        # If refresh failed or no refresh token, clear the session
        del sessions[session_id]
        return None
    
    return session["user_info"]

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "user-web-app"
    } 