from reporter.utils import get_all_responses, get_initial_response
from reporter.models import SearchParams
from fastmcp import Context

def register_tools(mcp):
    @mcp.tool()
    async def project_text_search(
        ctx: Context,
        search_params: SearchParams,
    ):
        """
        Tool to perform an advanced text search of the NIH RePORTER based on a given search string.
        
        Args:
            search_params (SearchParams): Search parameters including search term, years, agencies, organizations, and pi_name.
        Returns:
            dict: API response containing grant data
        """

        # Set query parameters
        limit = 50 
        include_fields = [
            "ProjectTitle",
            "FiscalYear",
            "PrincipalInvestigators",
            "ActivityCode",
            "ProjectNum",
            "AgencyIcAdmin",
            "CongDist",
            "AgencyCode",
            "AwardAmount",
            "Organization"
        ]

        # make the initial search 
        total, response = await get_initial_response(search_params, include_fields, limit)

        if total > 100:
            return {
                "error": f"Search still returns {total} results. Please provide more specific criteria.",
            }

        # Call the API 
        return await get_all_responses(search_params, include_fields, limit)
    
    @mcp.tool()
    async def get_all_projects_by_ic(search_params: SearchParams):
        """
            Tool to get an exhaustive list of projects for specific search critiera (such as NIH institute or center (IC) in a given year).
            
            Args:
                search_params (SearchParams): Search parameters including years, agencies
                
            Returns:
                dict: API response containing project IDs 
            """

        # Set query parameters 
        limit = 500
        include_fields = ["ProjectNum"]

        # Call the API 
        return await get_all_responses(search_params, include_fields, limit)
    
    @mcp.tool()
    async def get_project_details(search_params: SearchParams):
        """
        Tool to get detailed information about a specific project using its project number.
        
        Args:
            search_params (SearchParams): Search parameters including years, agencies, organizations, and pi_name.
                
        Returns:
            dict: API response containing detailed project information
        """

        limit = 25 
        include_fields = None 

        return await get_all_responses(search_params, include_fields, limit)
