"""
ServiceNow MCP Server

This module provides the main implementation of the ServiceNow MCP server.
"""

import argparse
import os
from typing import Dict, Union

import uvicorn
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, OAuthConfig, ApiKeyConfig, ServerConfig


def create_starlette_app(servicenow_mcp: ServiceNowMCP, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can serve the ServiceNow MCP server with SSE."""
    sse = SseServerTransport("/messages/")
    mcp_server = servicenow_mcp.mcp_server  # Get the actual MCP server

    async def handle_sse(request: Request) -> Response:
        # Get session ID from ServiceNow MCP server
        session_id = servicenow_mcp.session_id
        
        async def send_with_headers(message):
            # Add session headers to SSE responses
            if session_id and isinstance(message, dict) and message.get('type') == 'http.response.start':
                headers = message.get('headers', [])
                headers.extend([
                    (b'x-mcp-session-id', session_id.encode()),
                    (b'mcp-session-id', session_id.encode())
                ])
                message['headers'] = headers
            await request._send(message)  # noqa: SLF001
        
        async with sse.connect_sse(
            request.scope,
            request.receive,
            send_with_headers,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )
        
        return Response(status_code=200)

    class SessionHeaderMiddleware(BaseHTTPMiddleware):
        """Middleware to add session headers to all responses."""
        
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            session_id = servicenow_mcp.session_id
            if session_id:
                response.headers["x-mcp-session-id"] = session_id
                response.headers["mcp-session-id"] = session_id
            return response

    app = Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
    
    # Add middleware for session headers
    app.add_middleware(SessionHeaderMiddleware)
    
    return app


class ServiceNowSSEMCP(ServiceNowMCP):
    """
    ServiceNow MCP Server implementation.

    This class provides a Model Context Protocol (MCP) server for ServiceNow,
    allowing LLMs to interact with ServiceNow data and functionality.
    """

    def __init__(self, config: Union[Dict, ServerConfig]):
        """
        Initialize the ServiceNow MCP server.

        Args:
            config: Server configuration, either as a dictionary or ServerConfig object.
        """
        super().__init__(config)

    def start(self, host: str = "0.0.0.0", port: int = 8080):
        """
        Start the MCP server with SSE transport using Starlette and Uvicorn.

        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        # Create Starlette app with SSE transport
        starlette_app = create_starlette_app(self, debug=True)

        # Run using uvicorn
        uvicorn.run(starlette_app, host=host, port=port)


def create_servicenow_mcp(instance_url: str, auth_type: str = "basic", **auth_params):
    """
    Create a ServiceNow MCP server with configurable authentication.

    Args:
        instance_url: ServiceNow instance URL
        auth_type: Authentication type ("basic", "oauth", "api_key")
        **auth_params: Authentication parameters based on auth_type

    Returns:
        A configured ServiceNowMCP instance ready to use
    """
    
    if auth_type == "basic":
        auth_config = AuthConfig(
            type=AuthType.BASIC, 
            basic=BasicAuthConfig(
                username=auth_params["username"], 
                password=auth_params["password"]
            )
        )
    elif auth_type == "oauth":
        auth_config = AuthConfig(
            type=AuthType.OAUTH,
            oauth=OAuthConfig(
                client_id=auth_params["client_id"],
                client_secret=auth_params["client_secret"],
                username=auth_params["username"],
                password=auth_params["password"],
                token_url=auth_params.get("token_url")
            )
        )
    elif auth_type == "api_key":
        auth_config = AuthConfig(
            type=AuthType.API_KEY,
            api_key=ApiKeyConfig(
                api_key=auth_params["api_key"],
                header_name=auth_params.get("header_name", "X-ServiceNow-API-Key")
            )
        )
    else:
        raise ValueError(f"Unsupported auth_type: {auth_type}")

    config = ServerConfig(instance_url=instance_url, auth=auth_config)
    return ServiceNowSSEMCP(config)


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Run ServiceNow MCP SSE-based server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    args = parser.parse_args()

    auth_type = os.getenv("SERVICENOW_AUTH_TYPE", "basic")
    
    if auth_type == "basic":
        server = create_servicenow_mcp(
            instance_url=os.getenv("SERVICENOW_INSTANCE_URL"),
            auth_type="basic",
            username=os.getenv("SERVICENOW_USERNAME"),
            password=os.getenv("SERVICENOW_PASSWORD")
        )
    elif auth_type == "oauth":
        server = create_servicenow_mcp(
            instance_url=os.getenv("SERVICENOW_INSTANCE_URL"),
            auth_type="oauth",
            client_id=os.getenv("SERVICENOW_CLIENT_ID"),
            client_secret=os.getenv("SERVICENOW_CLIENT_SECRET"),
            username=os.getenv("SERVICENOW_USERNAME"),
            password=os.getenv("SERVICENOW_PASSWORD"),
            token_url=os.getenv("SERVICENOW_TOKEN_URL")
        )
    elif auth_type == "api_key":
        server = create_servicenow_mcp(
            instance_url=os.getenv("SERVICENOW_INSTANCE_URL"),
            auth_type="api_key",
            api_key=os.getenv("SERVICENOW_API_KEY"),
            header_name=os.getenv("SERVICENOW_API_KEY_HEADER", "X-ServiceNow-API-Key")
        )
    else:
        raise ValueError(f"Unsupported SERVICENOW_AUTH_TYPE: {auth_type}")
    
    server.start(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
