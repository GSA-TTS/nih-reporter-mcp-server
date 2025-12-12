from reporter.utils import get_all_responses, get_initial_response
from reporter.models import SearchParams
from fastmcp import Context

def register_tools(mcp):
    @mcp.tool()
    async def find_project_ids(
        ctx: Context,
        search_params: SearchParams,
    ):
        """
        Tool to perform a search of the NIH RePORTER API and return project IDs based on search criteria.
        
        Args:
            search_params (SearchParams): Search parameters including search term, years, agencies, organizations, and pi_name.
        Returns:
            dict: API response containing grant ids 
        """

        # Set query parameters
        limit = 500 
        include_fields = [
            "ProjectNum",
        ]

        # # Call the API 
        return await get_all_responses(search_params, include_fields, limit)
    
    @mcp.tool()
    async def get_project_descriptions(search_params: SearchParams):
        """
        Tool to get all available project information including full title and abstract text.
        Use this to answer questions related to the content of the project. 
        
        Args:
            search_params (SearchParams): project ID numbers 
                
        Returns:
            dict: API response containing full project information including title and abstract text 
        """

        limit = 100 
        include_fields = None 

        return await get_all_responses(search_params, include_fields, limit)
    
    @mcp.tool()
    async def get_project_information(search_params: SearchParams):
        """
        Tool to get specified metadata for a project based on project number. 
        Use this to answer questions about award amounts, organizations, PIs, etc.
        
        Args:
            search_params (SearchParams): project ID numbers 
                
        Returns:
            dict: API response with specified project metadata
        """

        limit = 500 
        include_fields = [
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

        # Call the API 
        return await get_all_responses(search_params, include_fields, limit)
