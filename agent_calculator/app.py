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
import asyncio
import uuid

# A2A imports
from a2a.server.agent_execution import AgentExecutor
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, Message, TextPart
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue

# Local imports
from calculator import TaxCalculator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Agent Calculator Service")
security = HTTPBearer()

# Initialize the tax calculator
tax_calculator = TaxCalculator()

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


class TaxCalculatorAgentExecutor(AgentExecutor):
    """A2A Agent Executor for the Tax Calculator service."""
    
    def __init__(self, calculator: TaxCalculator):
        """Initialize with a tax calculator instance."""
        self.calculator = calculator
        super().__init__()
    
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Execute a task represented by a message and put results in the event queue.
        This is the main execution method required by the AgentExecutor interface.
        
        Args:
            context: The A2A request context containing the message and metadata
            event_queue: Event queue to put results in for streaming to the client
        """
        logger.info("A2A Tax Calculator executing task")
        
        try:
            # Extract text content from the context
            user_input = context.get_user_input()
            logger.info(f"User input: {user_input}")
            
            # Perform tax calculation
            calculation_result = self.calculator.calculate_tax()
            
            # Analyze user input to provide relevant response
            user_input_lower = user_input.lower()
            
            if "structured" in user_input_lower or "json" in user_input_lower or "machine readable" in user_input_lower:
                # Return structured JSON data instead of formatted text
                response_text = json.dumps(calculation_result['tax_result'], indent=2)

            elif "rate" in user_input_lower or "percentage" in user_input_lower:
                response_text = f"Current Tax Rates:\n"
                response_text += f"• Federal Tax Rate: {calculation_result['tax_result']['federal_tax_rate']:.1%}\n"
                response_text += f"• State Tax Rate: {calculation_result['tax_result']['state_tax_rate']:.1%}\n"
                response_text += f"• Effective Tax Rate: {calculation_result['tax_result']['effective_tax_rate']:.1%}\n"
                
            elif "bracket" in user_input_lower:
                response_text = "Current Tax Brackets:\n"
                for bracket in calculation_result['tax_result']['tax_brackets']:
                    if bracket['max'] is None:
                        response_text += f"• ${bracket['min']:,}+: {bracket['rate']:.1%}\n"
                    else:
                        response_text += f"• ${bracket['min']:,} - ${bracket['max']:,}: {bracket['rate']:.1%}\n"
                        
            elif "deduction" in user_input_lower:
                response_text = "Available Deductions:\n"
                response_text += f"• Standard Deduction: ${calculation_result['tax_result']['deductions']['standard_deduction']:,}\n"
                response_text += f"• Itemized Deductions Available: Mortgage Interest, Property Tax, Charitable Contributions\n"
                
            elif "credit" in user_input_lower:
                response_text = "Available Tax Credits:\n"
                response_text += f"• Child Tax Credit: ${calculation_result['tax_result']['credits']['child_tax_credit']:,}\n"
                response_text += f"• Earned Income Credit: Available based on income level\n"
                
            else:
                # Default comprehensive response
                response_text = f"{calculation_result['message']}\n\nTax Calculation Summary:\n"
                response_text += f"• Federal Tax Rate: {calculation_result['tax_result']['federal_tax_rate']:.1%}\n"
                response_text += f"• State Tax Rate: {calculation_result['tax_result']['state_tax_rate']:.1%}\n"
                response_text += f"• Effective Tax Rate: {calculation_result['tax_result']['effective_tax_rate']:.1%}\n"
                response_text += f"• Standard Deduction: ${calculation_result['tax_result']['deductions']['standard_deduction']:,}\n"
                response_text += f"• Child Tax Credit: ${calculation_result['tax_result']['credits']['child_tax_credit']:,}\n"
                
                # Add tax brackets info
                response_text += "\nTax Brackets:\n"
                for bracket in calculation_result['tax_result']['tax_brackets']:
                    if bracket['max'] is None:
                        response_text += f"• ${bracket['min']:,}+: {bracket['rate']:.1%}\n"
                    else:
                        response_text += f"• ${bracket['min']:,} - ${bracket['max']:,}: {bracket['rate']:.1%}\n"
            
            logger.info("A2A Tax calculation completed successfully")
            
            # Send the single response (no streaming)
            await event_queue.enqueue_event(Message(
                messageId=str(uuid.uuid4()),
                role="agent",
                parts=[TextPart(
                    type="text",
                    text=response_text
                )]
            ))
            
        except Exception as e:
            logger.error(f"Error in A2A tax calculation: {str(e)}")
            error_message = f"Sorry, I encountered an error while calculating tax information: {str(e)}"
            
            await event_queue.enqueue_event(Message(
                messageId=str(uuid.uuid4()),
                role="agent",
                parts=[TextPart(
                    type="text",
                    text=error_message
                )]
            ))
    
    async def cancel(self, task_id: str) -> bool:
        """
        Cancel a running task by task ID.
        
        Args:
            task_id: The ID of the task to cancel
            
        Returns:
            bool: True if task was successfully cancelled, False otherwise
        """
        logger.info(f"A2A Tax Calculator received cancel request for task: {task_id}")
        # For this simple calculator agent, we don't have long-running tasks to cancel
        # In a real implementation, you would track running tasks and cancel them here
        logger.info(f"Task {task_id} cancellation completed (no-op for this agent)")
        return True

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
        
        # Use the tax calculator with the token context
        response = tax_calculator.calculate_tax(context=decoded_token)
        logger.info("Sending response:")
        logger.info(f"Response data: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Error in calculate_tax: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating tax: {str(e)}")


# A2A Setup
def setup_a2a_server():
    """Set up the A2A server with proper FastAPI integration."""
    
    # Create agent card
    agent_card = AgentCard(
        name="Tax Calculator Agent",
        description="Provides tax calculation information including rates, brackets, deductions, and credits",
        url="http://localhost:8003",
        version="1.0.0",
        capabilities={
            "streaming": False,  # Disable streaming by default
            "pushNotifications": False,
            "stateTransitionHistory": False
        },
        defaultInputModes=["text", "text/plain"],
        defaultOutputModes=["text", "text/plain"],
        skills=[{
            "id": "tax_calculation",
            "name": "Tax Calculation",
            "description": "Calculate tax rates, brackets, deductions, and credits",
            "tags": ["tax", "calculation", "finance"],
            "examples": [
                "What are the current tax rates?",
                "Calculate tax information",
                "Show me tax brackets",
                "What deductions are available?"
            ]
        }]
    )
    
    # Create A2A components
    task_store = InMemoryTaskStore()
    agent_executor = TaxCalculatorAgentExecutor(tax_calculator)
    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
    )
    
    # Create A2A FastAPI app and integrate with existing app
    a2a_app = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )
    
    # Get the FastAPI app from A2A and merge routes
    a2a_fastapi_app = a2a_app.build()
    
    # Add A2A routes to our existing FastAPI app
    app.include_router(a2a_fastapi_app.router, prefix="/a2a")
    
    # Add agent card endpoint
    @app.get("/a2a/.well-known/agent.json")
    async def get_agent_card():
        """Return the agent card for A2A discovery."""
        return agent_card.model_dump()
    
    logger.info("A2A server properly integrated with FastAPI")
    logger.info("Agent card available at /a2a/.well-known/agent.json")
    logger.info("A2A RPC endpoint available at /a2a/")


# Set up A2A server
setup_a2a_server()

if __name__ == "__main__":
    logger.info(f"Agent Calculator app initialized")
    logger.info(f"REST API available at http://localhost:{PORT}/api/calculate")
    logger.info(f"A2A Agent available at http://localhost:{PORT}/a2a")
    logger.info(f"A2A Agent Card available at http://localhost:{PORT}/a2a/.well-known/agent.json")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT) 