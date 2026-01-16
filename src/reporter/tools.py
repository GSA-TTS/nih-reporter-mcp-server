from reporter.utils import get_all_responses, get_initial_response, get_project_distributions
from reporter.models import SearchParams, ProjectNum
from fastmcp import Context

def register_tools(mcp):
    @mcp.tool()
    async def find_project_ids(
        ctx: Context,
        search_params: SearchParams,
    ):
        """
        Tool to perform a search of the NIH RePORTER API and return project IDs based on search criteria.
        
        This is the primary search tool - use it to find grants matching your criteria.
        Returns overview statistics and up to 500 project IDs. If more results exist,
        the tool will indicate this and you can help the user refine their search.
        
        Args:
            search_params (SearchParams): Search parameters including search term, years, agencies, organizations, and pi_name.
        
        Returns:
            dict: API response containing:
            - total_projects: Total number of matching projects in database
            - returned_projects: Number of project IDs returned (max 500)
            - project_ids: List of project ID numbers
            - year_distribution: Breakdown of projects by fiscal year
            - institute_distribution: Breakdown by NIH institute/center
            - activity_code_distribution: Breakdown by activity code (grant type)
            - has_more_results: Whether additional projects exist beyond the 500 returned
        """
        
        # Get data with fields needed for distributions
        include_fields = [
            "ProjectNum",
            "FiscalYear",
            "AgencyIcAdmin",  # NIH Institute/Center
            "ActivityCode",   # Grant type (R01, F32, etc.)
        ]
        
        # Get initial response (limit 500 for initial search)
        limit = 500
        total_projects, all_results = await get_initial_response(
            search_params,
            include_fields,
            limit
        )
        
        project_ids, year_dist, ic_dist, activity_dist = get_project_distributions(all_results)
        
        return {
            "total_projects": total_projects,
            "returned_projects": len(project_ids),
            "project_ids": project_ids,
            "year_distribution": dict(sorted(year_dist.items(), reverse=True)),
            "institute_distribution": dict(ic_dist.most_common(15)),
            "activity_code_distribution": dict(activity_dist.most_common(15)),
            "has_more_results": total_projects > len(project_ids),
        }
        
    @mcp.tool()
    async def get_project_descriptions(project_ids: list[ProjectNum]):
        """
        Tool to get all available project information including full title and abstract text.
        Use this to answer questions related to the content of the project. 
        
        Args:
            project_ids (list[ProjectNum]): project ID numbers 
                
        Returns:
            dict: API response containing full project information including title and abstract text 
        """

        limit = 25 
        include_fields = None 

        # add project_ids to a search_params object
        search_params = SearchParams(
            project_nums=project_ids
        )

        return await get_all_responses(search_params, include_fields, limit)
        
    @mcp.tool()
    async def get_project_information(project_ids: list[ProjectNum]):
        """
        Tool to get specified metadata for a project based on project number. 
        Use this to answer questions about award amounts, organizations, PIs, etc.
        
        Args:
            project_ids (list[ProjectNum]): project ID numbers 
                
        Returns:
            dict: API response with specified project metadata
        """

        limit = 100 
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

        # add project_ids to a search_params object
        search_params = SearchParams(
            project_nums=project_ids
        )

        # Call the API 
        return await get_all_responses(search_params, include_fields, limit)
