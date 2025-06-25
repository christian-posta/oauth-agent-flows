#!/usr/bin/env python3
"""
Test client using the official a2a-json-rpc library.
This demonstrates the proper way to use the A2A protocol with the official SDK.

Install required dependencies:
pip install a2a-json-rpc httpx
"""

import asyncio
import uuid
from typing import Optional

try:
    from a2a_json_rpc import A2AClient
    from a2a_json_rpc.models import MessageRequest, Message, TextPart
except ImportError:
    print("Error: a2a-json-rpc library not installed.")
    print("Install it with: pip install a2a-json-rpc")
    exit(1)


class A2ATaxCalculatorClient:
    """Client for testing the Tax Calculator A2A Agent using the official library."""
    
    def __init__(self, base_url: str):
        """Initialize the client with the agent's base URL."""
        self.base_url = base_url.rstrip('/')
        self.a2a_endpoint = f"{self.base_url}/a2a/"
        self.client = A2AClient(self.a2a_endpoint)
    
    async def get_agent_info(self) -> dict:
        """Get agent card information."""
        try:
            # The A2A client should handle agent card discovery
            agent_card_url = f"{self.base_url}/a2a/.well-known/agent.json"
            import httpx
            async with httpx.AsyncClient() as http_client:
                response = await http_client.get(agent_card_url)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Could not fetch agent card: {e}")
            return {}
    
    async def send_message(self, text: str) -> Optional[dict]:
        """Send a message to the agent using the official A2A library."""
        try:
            # Create the message request using the official models
            message = Message(
                messageId=str(uuid.uuid4()),
                role="user",
                parts=[TextPart(type="text", text=text)]
            )
            
            request = MessageRequest(
                message=message
            )
            
            print(f"Sending message: {text}")
            
            # Send the message using the official client
            response = await self.client.send_message(request)
            
            print(f"Response received: {response}")
            return response
            
        except Exception as e:
            print(f"Error sending message: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def send_streaming_message(self, text: str):
        """Send a streaming message to the agent."""
        try:
            # Create the message request
            message = Message(
                messageId=str(uuid.uuid4()),
                role="user", 
                parts=[TextPart(type="text", text=text)]
            )
            
            request = MessageRequest(
                message=message
            )
            
            print(f"Sending streaming message: {text}")
            
            # Send streaming message
            async for chunk in self.client.send_streaming_message(request):
                print(f"Streaming chunk: {chunk}")
                
        except Exception as e:
            print(f"Error with streaming message: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Test the A2A Tax Calculator Agent using the official library."""
    
    agent_url = "http://localhost:8003"
    client = A2ATaxCalculatorClient(agent_url)
    
    print("=" * 60)
    print("A2A Tax Calculator Agent Test (Official Library)")
    print("=" * 60)
    
    try:
        # 1. Get agent information
        print("\n1. Getting agent information...")
        agent_info = await client.get_agent_info()
        if agent_info:
            print(f"Agent Name: {agent_info.get('name', 'Unknown')}")
            print(f"Agent Description: {agent_info.get('description', 'No description')}")
            print(f"Agent Capabilities: {agent_info.get('capabilities', {})}")
        
        # 2. Send basic messages
        print("\n2. Sending basic tax calculation request...")
        response = await client.send_message("What are the current tax rates?")
        
        if response:
            print("Agent response received successfully!")
        
        # 3. Test different questions
        questions = [
            "Show me the tax brackets",
            "What deductions are available?",
            "Calculate tax information for me",
            "What is the effective tax rate?"
        ]
        
        for i, question in enumerate(questions, 3):
            print(f"\n{i}. Asking: {question}")
            response = await client.send_message(question)
            if response:
                print("Response received!")
        
        # 4. Test streaming if supported
        print(f"\n{len(questions) + 3}. Testing streaming message...")
        await client.send_streaming_message("Explain the tax calculation process step by step")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 