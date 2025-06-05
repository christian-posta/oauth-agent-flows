from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Planner Service")
security = HTTPBearer()

@app.post("/generate-plan")
async def generate_plan(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Generate a financial plan based on the user's token."""
    try:
        # Get the token from the Authorization header
        token = credentials.credentials
        
        # Decode and verify the token
        # In a real implementation, you would verify the token signature
        decoded_token = jwt.get_unverified_claims(token)
        
        # Log the decoded token
        print("Decoded token:", decoded_token)
        
        # Return a simple response
        return {
            "message": "You called me",
            "token_info": decoded_token
        }
        
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 