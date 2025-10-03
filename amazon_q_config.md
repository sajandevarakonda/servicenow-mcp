# Amazon Q Integration Configuration

## MCP Session Headers

The ServiceNow MCP server now includes session ID headers in all responses to support Amazon Q integration:

- `x-mcp-session-id`: Unique session identifier
- `mcp-session-id`: Duplicate header for compatibility

## Environment Variables

Set these environment variables for Amazon Q integration:

```bash
# Required ServiceNow configuration
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password
SERVICENOW_AUTH_TYPE=basic

# Optional: Custom session ID (auto-generated if not provided)
MCP_SESSION_ID=your-custom-session-id

# Optional: Tool package selection
MCP_TOOL_PACKAGE=service_desk
```

## Claude Desktop Configuration

Update your Claude Desktop configuration to include the session headers:

```json
{
  "mcpServers": {
    "ServiceNow": {
      "command": "/path/to/servicenow-mcp/.venv/bin/python",
      "args": [
        "-m",
        "servicenow_mcp.cli"
      ],
      "env": {
        "SERVICENOW_INSTANCE_URL": "https://your-instance.service-now.com",
        "SERVICENOW_USERNAME": "your-username",
        "SERVICENOW_PASSWORD": "your-password",
        "SERVICENOW_AUTH_TYPE": "basic",
        "MCP_SESSION_ID": "amazon-q-session-123"
      }
    }
  }
}
```

## SSE Server Mode

For SSE server mode with session headers:

```bash
# Start SSE server with session headers
MCP_SESSION_ID=amazon-q-session python -m servicenow_mcp.server_sse --host=0.0.0.0 --port=8080
```

## Verification

Run the test script to verify session headers:

```bash
python test_session_headers.py
```

The output should show the generated session ID and confirm that annotations are present in responses.