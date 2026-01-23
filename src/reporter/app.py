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


# ASGI app for remote deployment (gunicorn/uvicorn imports this)
# Example: gunicorn reporter.app:app
app = mcp.http_app(stateless_http=True)


if __name__ == "__main__":
    # Running directly: use stdio for local MCP client (Claude Desktop, etc.)
    # Remote deployments use the ASGI app above via gunicorn/uvicorn
    mcp.run(transport="stdio")




