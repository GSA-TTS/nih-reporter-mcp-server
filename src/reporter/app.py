import os

from fastmcp import FastMCP
from reporter.tools import register_tools
from reporter.prompts import register_prompts
from starlette.responses import JSONResponse

# Initialize FastMCP server
mcp = FastMCP("reporter")

# Register custom tools
register_tools(mcp)

# Register custom prompts
register_prompts(mcp)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

# Create ASGI app for deployment
app = mcp.http_app(stateless_http=True)


def is_remote_environment() -> bool:
    """Detect if running in a remote/cloud environment."""
    # Cloud Foundry (cloud.gov)
    if os.environ.get("VCAP_APPLICATION"):
        return True
    # Generic environment variable override
    if os.environ.get("MCP_TRANSPORT") == "http":
        return True
    if os.environ.get("ENVIRONMENT") in ("production", "staging", "remote"):
        return True
    return False


if __name__ == "__main__":
    if is_remote_environment():
        # HTTP transport for remote/cloud deployment
        port = int(os.environ.get("PORT", 8000))
        mcp.run(transport="http", host="0.0.0.0", port=port)
    else:
        # stdio transport for local development
        mcp.run(transport="stdio")




