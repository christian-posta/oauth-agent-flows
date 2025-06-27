#!/usr/bin/env python3
"""
Test script for the MCP Tax Calculator Server
"""

import asyncio
import json
import sys
import os
from contextlib import AsyncExitStack

from mcp import stdio_client, StdioServerParameters, ClientSession

async def test_mcp_server():
    """Test the MCP tax calculator server."""
    print("Testing MCP Tax Calculator Server...")
    
    # Get the path to the MCP server
    server_path = os.path.join(os.path.dirname(__file__), "mcp_tax_calculator_server.py")
    
    async with AsyncExitStack() as exit_stack:
        try:
            # Create MCP server parameters
            server_params = StdioServerParameters(
                command="python",
                args=[server_path],
                env=None
            )
            
            # Create stdio transport
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            read_stream, write_stream = stdio_transport
            
            print("✓ MCP client connected successfully")
            
            # Create client session
            session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
            
            print("Initializing MCP session...")
            await session.initialize()
            print("✓ MCP session initialized successfully")
            
            # List available tools
            response = await session.list_tools()
            tools = response.tools
            print("✓ Connected to server with tools:", [tool.name for tool in tools])
            
            # Test calculate_tax tool
            print("\nTesting calculate_tax tool...")
            result = await session.call_tool("calculate_tax", {})
            print("✓ Received response from calculate_tax tool")
            print(f"✓ calculate_tax result: {result}")
            
            # Test get_tax_brackets tool
            print("\nTesting get_tax_brackets tool...")
            result = await session.call_tool("get_tax_brackets", {})
            print("✓ Received response from get_tax_brackets tool")
            print(f"✓ get_tax_brackets result: {result}")
            
            # Test get_tax_rates tool
            print("\nTesting get_tax_rates tool...")
            result = await session.call_tool("get_tax_rates", {})
            print("✓ Received response from get_tax_rates tool")
            print(f"✓ get_tax_rates result: {result}")
            
            print("\n🎉 All MCP server tests passed!")
            
        except Exception as e:
            print(f"❌ Error testing MCP server: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    sys.exit(0 if success else 1) 