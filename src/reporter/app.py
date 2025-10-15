from fastmcp import FastMCP
from reporter.tools import register_tools 
from starlette.responses import JSONResponse

# Initialize FastMCP server
mcp = FastMCP("reporter")

# Register custom tools 
register_tools(mcp)

# Health check endpoint
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

# Create ASGI app for deployment
app = mcp.http_app(stateless_http=True)

# Run the server with stdio transport for local testing
# if __name__ == "__main__":
#     # Initialize and run the server
#     mcp.run(transport='stdio')

# Run the server with HTTP transport for external access
# if __name__ == "__main__":
#     mcp.run(transport="http", host="0.0.0.0", port=8000)




