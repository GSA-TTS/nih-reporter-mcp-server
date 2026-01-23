from typing import Optional, List
from reporter.utils import get_all_responses, get_initial_response, get_project_distributions
from reporter.models import SearchParams, ProjectNum, NIHAgency, StateCode, IncludeField
from fastmcp import Context

def register_tools(mcp):
    @mcp.tool()
    async def search_projects(
        ctx: Context,
        search_params: SearchParams,
    ):
        """
        Tool to perform an initial search of the NIH RePORTER API and return the count of matching projects.

        Use this tool first to see how many projects match your search criteria before
        retrieving detailed results.

        Args:
            search_params (SearchParams): Search parameters including search term, years, agencies, organizations, and pi_name.

        Returns:
            dict: API response containing:
            - total_projects: Total number of matching projects in database
        """

        # Minimal fields needed - just need the count from meta
        include_fields = [IncludeField.PROJECT_NUM.value]

        # Get initial response with limit of 1 (we only need the count)
        total_projects, _ = await get_initial_response(
            search_params,
            include_fields,
            limit=1
        )

        return {
            "total_projects": total_projects,
        }

    @mcp.tool()
    async def refine_search(
        ctx: Context,
        search_params: SearchParams,
        filter_years: Optional[List[int]] = None,
        filter_agencies: Optional[List[NIHAgency]] = None,
        filter_activity_codes: Optional[List[str]] = None,
        filter_states: Optional[List[StateCode]] = None,
    ):
        """
        Tool to refine search results by applying additional filters.

        Use this after search_projects to narrow down results based on distributions.
        Pass the original search_params along with filter parameters to see how
        adding constraints affects the result count.

        Args:
            search_params (SearchParams): The base search criteria from your initial search.
            filter_years (Optional[List[int]]): Filter to specific fiscal years (e.g., [2023, 2024]).
            filter_agencies (Optional[List[NIHAgency]]): Filter to specific NIH institutes (e.g., [NCI, NIMH]).
            filter_activity_codes (Optional[List[str]]): Filter to specific grant types (e.g., ["R01", "F32"]).
            filter_states (Optional[List[StateCode]]): Filter to specific states (e.g., [CA, NY]).

        Returns:
            dict: API response containing:
            - total_projects: Total number of matching projects after refinement
            - year_distribution: Breakdown of projects by fiscal year
            - institute_distribution: Breakdown by NIH institute/center
            - activity_code_distribution: Breakdown by activity code (grant type)
        """

        # Apply filters to search_params
        if filter_years:
            search_params.years = filter_years
        if filter_agencies:
            search_params.agencies = filter_agencies
        if filter_activity_codes:
            search_params.activity_codes = filter_activity_codes
        if filter_states:
            search_params.org_states = filter_states

        # Get results with distribution fields
        include_fields = [
            IncludeField.PROJECT_NUM.value,
            IncludeField.FISCAL_YEAR.value,
            IncludeField.AGENCY_IC_ADMIN.value,
            IncludeField.ACTIVITY_CODE.value,
        ]
        limit = 500

        total_projects, all_results = await get_initial_response(
            search_params,
            include_fields,
            limit
        )

        _, year_dist, ic_dist, activity_dist = get_project_distributions(all_results)

        return {
            "total_projects": total_projects,
            "year_distribution": dict(sorted(year_dist.items(), reverse=True)),
            "institute_distribution": dict(ic_dist.most_common(15)),
            "activity_code_distribution": dict(activity_dist.most_common(15)),
        }

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
            IncludeField.PROJECT_NUM.value,
            IncludeField.FISCAL_YEAR.value,
            IncludeField.AGENCY_IC_ADMIN.value,
            IncludeField.ACTIVITY_CODE.value,
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
    async def get_project_information(
        project_ids: list[ProjectNum],
        include_fields: List[IncludeField],
    ):
        """
        Tool to get specified metadata for a project based on project number.
        Use this to answer questions about award amounts, organizations, PIs, etc.

        Args:
            project_ids (list[ProjectNum]): project ID numbers
            include_fields (List[IncludeField]): List of fields to return from the API.
                Choose fields relevant to the query (e.g., AWARD_AMOUNT for funding questions,
                PRINCIPAL_INVESTIGATORS for PI questions, ORGANIZATION for institution questions).

        Returns:
            dict: API response with specified project metadata
        """

        limit = 100

        # Convert IncludeField enums to their string values
        field_values = [f.value for f in include_fields]

        # add project_ids to a search_params object
        search_params = SearchParams(
            project_nums=project_ids
        )

        # Call the API
        return await get_all_responses(search_params, field_values, limit)
