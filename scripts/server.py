from fastmcp import FastMCP
from starlette.responses import JSONResponse

mcp = FastMCP("My Server")

@mcp.tool
def process_data(input: str) -> str:
    """Process data on the server"""
    return f"Processed: {input}"

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8001)

    

