#!/usr/bin/env python3
"""
Test client for the A2A Tax Calculator Agent.
This client uses the proper JSON-RPC 2.0 format expected by the A2A protocol.
"""

import requests
import json
import uuid
from typing import Dict, Any

class A2ATestClient:
    """Simple A2A client that uses JSON-RPC 2.0 format."""
    
    def __init__(self, base_url: str):
        """Initialize the client with the agent's base URL."""
        self.base_url = base_url.rstrip('/')
        self.a2a_endpoint = f"{self.base_url}/a2a/"
        self.agent_card_url = f"{self.base_url}/a2a/.well-known/agent.json"
    
    def get_agent_card(self) -> Dict[str, Any]:
        """Fetch the agent card to discover agent capabilities."""
        response = requests.get(self.agent_card_url)
        response.raise_for_status()
        return response.json()
    
    def send_message(self, text: str, request_id: str = None) -> Dict[str, Any]:
        """
        Send a message to the agent using proper A2A JSON-RPC 2.0 format.
        
        Args:
            text: The message text to send
            request_id: Optional request ID (generates one if not provided)
            
        Returns:
            The agent's response
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Generate a unique message ID
        message_id = str(uuid.uuid4())
        
        # Construct the JSON-RPC 2.0 request in the format expected by A2A
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "message/send",
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            }
        }
        
        print(f"Sending request to: {self.a2a_endpoint}")
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        # Send the request
        response = requests.post(
            self.a2a_endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            print(f"Error response body: {response.text}")
            response.raise_for_status()
        
        response_data = response.json()
        print(f"Response data: {json.dumps(response_data, indent=2)}")
        
        return response_data
    
    def send_message_stream(self, text: str, request_id: str = None) -> None:
        """
        Send a streaming message to the agent.
        
        Args:
            text: The message text to send
            request_id: Optional request ID (generates one if not provided)
        """
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        # Generate a unique message ID
        message_id = str(uuid.uuid4())
        
        # Construct the JSON-RPC 2.0 request for streaming
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "message/stream",
            "params": {
                "message": {
                    "messageId": message_id,
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": text
                        }
                    ]
                }
            }
        }
        
        print(f"Sending streaming request to: {self.a2a_endpoint}")
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        
        # Send the streaming request
        response = requests.post(
            self.a2a_endpoint,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream"
            },
            stream=True
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error response body: {response.text}")
            response.raise_for_status()
        
        # Process streaming response
        print("Streaming response:")
        for line in response.iter_lines(decode_unicode=True):
            if line:
                print(f"Stream data: {line}")


def main():
    """Test the A2A Tax Calculator Agent."""
    
    # Initialize the client
    agent_url = "http://localhost:8003"  # Your agent's URL
    client = A2ATestClient(agent_url)
    
    print("=" * 60)
    print("A2A Tax Calculator Agent Test Client")
    print("=" * 60)
    
    try:
        # 1. Discover the agent
        print("\n1. Discovering agent capabilities...")
        agent_card = client.get_agent_card()
        print(f"Agent Name: {agent_card.get('name', 'Unknown')}")
        print(f"Agent Description: {agent_card.get('description', 'No description')}")
        print(f"Agent Capabilities: {agent_card.get('capabilities', {})}")
        
        # 2. Send a basic message
        print("\n2. Sending basic tax calculation request...")
        response = client.send_message("What are the current tax rates?")
        
        # Parse the response
        if "result" in response:
            result = response["result"]
            if isinstance(result, dict):
                if "parts" in result:
                    # Direct message response
                    for part in result["parts"]:
                        if part.get("type") == "text":
                            print(f"Agent Response: {part.get('text', '')}")
                elif "artifacts" in result:
                    # Task-based response with artifacts
                    print("Agent completed task with artifacts:")
                    for artifact in result["artifacts"]:
                        for part in artifact.get("parts", []):
                            if part.get("type") == "text":
                                print(f"Artifact text: {part.get('text', '')}")
        
        # 3. Test streaming if supported
        if agent_card.get("capabilities", {}).get("streaming", False):
            print("\n3. Testing streaming response...")
            client.send_message_stream("Calculate tax information and explain the process")
        else:
            print("\n3. Streaming not supported by this agent")
        
        # 4. Test additional questions
        print("\n4. Asking about tax brackets...")
        response = client.send_message("Show me the tax brackets")
        
        if "result" in response:
            result = response["result"]
            if isinstance(result, dict) and "parts" in result:
                for part in result["parts"]:
                    if part.get("type") == "text":
                        print(f"Tax Brackets Response: {part.get('text', '')}")
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to agent at {agent_url}")
        print("Make sure your agent is running with: ./run-local.sh")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 