from fastmcp import FastMCP
from reporter.utils import get_all_responses, get_total_amount, search_nih_reporter
from reporter.models import SearchParams, ProjectNum
from starlette.responses import JSONResponse

# Initialize FastMCP server
mcp = FastMCP("reporter",stateless_http=True)

@mcp.tool()
async def project_text_search(search_params: SearchParams):
    """
    Tool to perform an advanced text search of the NIH RePORTER based on a given search string.
    
    Args:
        search_params (SearchParams): Search parameters including search term, years, agencies, organizations, and pi_name.
    Returns:
        dict: API response containing grant data
    """

    # Set query parameters
    limit = 50 
    include_fields = ["ProjectTitle","FiscalYear","PrincipalInvestigators","ActivityCode","ProjectNum","AgencyIcAdmin","CongDist","AgencyCode","AwardAmount","Organization"]

    # Call the API 
    return await get_all_responses(search_params, include_fields, limit)


@mcp.tool()
async def funding_by_organization(search_params: SearchParams):
    """
        Tool to get amount of funding by organization for a given year (or years) and agency (or agencies)
        
        Args:
            search_params (SearchParams): Search parameters including years, agencies, organizations, and pi_name.
            
        Returns:
            dict: API response containing grant data
        """

    # Set query parameters 
    limit = 500
    include_fields = ["ProjectNum","AwardAmount"]

    # Call the API 
    response = await get_all_responses(search_params, include_fields, limit)

    return get_total_amount(response)

@mcp.tool()
async def get_project_details(search_params: SearchParams):
    """
    Tool to get detailed information about a specific project using its project number.
    
    Args:
        search_params (SearchParams): Search parameters including years, agencies, organizations, and pi_name.
            
    Returns:
        dict: API response containing detailed project information
    """

    limit = 10 
    include_fields = None 

    return await get_all_responses(search_params, include_fields, limit)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "mcp-server"})

# Run the server with stdio transport for local testing
# if __name__ == "__main__":
#     # Initialize and run the server
#     mcp.run(transport='stdio')

# Run the server with HTTP transport for external access
# if __name__ == "__main__":
#     mcp.run(transport="http", host="0.0.0.0", port=8000)

app = mcp.http_app()


