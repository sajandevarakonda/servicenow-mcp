#!/usr/bin/env python3
"""
Test script to verify MCP session headers are included in responses.
"""

import asyncio
import json
import os
from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import ServerConfig, AuthConfig, AuthType, BasicAuthConfig

async def test_session_headers():
    """Test that session headers are included in MCP responses."""
    
    # Create a minimal config for testing
    config = ServerConfig(
        instance_url="https://test.service-now.com",
        auth=AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(
                username="test_user",
                password="test_pass"
            )
        ),
        debug=True
    )
    
    # Create ServiceNow MCP server
    mcp_server = ServiceNowMCP(config)
    
    print(f"Generated session ID: {mcp_server.session_id}")
    
    # Test list_tools
    tools = await mcp_server._list_tools_impl()
    print(f"Available tools: {len(tools)}")
    
    # Test call_tool with list_tool_packages
    try:
        result = await mcp_server._call_tool_impl("list_tool_packages", {"random_string": "test"})
        print(f"Tool call result type: {type(result)}")
        print(f"Result content: {result[0].text[:200]}...")
        
        # Check if annotations are present
        if hasattr(result[0], 'annotations') and result[0].annotations:
            print(f"Session annotations: {result[0].annotations}")
        else:
            print("No annotations found in response")
            
    except Exception as e:
        print(f"Error calling tool: {e}")

if __name__ == "__main__":
    asyncio.run(test_session_headers())