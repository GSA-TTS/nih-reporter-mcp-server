from typing import List
from reporter.utils import get_all_responses, get_initial_response, get_project_distributions
from reporter.models import SearchParams, ProjectNum, IncludeField
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
            search_params (SearchParams): Search parameters including search term, years, agencies, organizations, pi_name, po_names, and award_types.

        Returns:
            dict: API response containing:
            - total_projects: Total number of matching projects in database
            - year_distribution: Breakdown of projects by fiscal year
            - institute_distribution: Breakdown by NIH institute/center
            - activity_code_distribution: Breakdown by activity code (grant type)
            - organization_distribution: Breakdown by institution/organization
            - funding_mechanism_distribution: Breakdown by funding mechanism
            - active_status_distribution: Breakdown of active vs inactive projects
            - award_amount_stats: Funding statistics (total, average, min, max)
        """

        # Get data with fields needed for distributions
        include_fields = [
            IncludeField.PROJECT_NUM.value,
            IncludeField.FISCAL_YEAR.value,
            IncludeField.AGENCY_IC_ADMIN.value,
            IncludeField.ACTIVITY_CODE.value,
            IncludeField.ORGANIZATION.value,
            IncludeField.FUNDING_MECHANISM.value,
            IncludeField.IS_ACTIVE.value,
            IncludeField.AWARD_AMOUNT.value,
        ]

        # Get initial response (limit 500 for distribution sampling)
        limit = 500
        total_projects, all_results = await get_initial_response(
            search_params,
            include_fields,
            limit
        )

        distributions = get_project_distributions(all_results)

        return {
            "total_projects": total_projects,
            "year_distribution": dict(sorted(distributions["year_distribution"].items(), reverse=True)),
            "institute_distribution": dict(distributions["institute_distribution"].most_common(15)),
            "activity_code_distribution": dict(distributions["activity_code_distribution"].most_common(15)),
            "organization_distribution": dict(distributions["organization_distribution"].most_common(15)),
            "funding_mechanism_distribution": dict(distributions["funding_mechanism_distribution"].most_common()),
            "active_status_distribution": dict(distributions["active_status_distribution"]),
            "award_amount_stats": distributions["award_amount_stats"],
        }

    @mcp.tool()
    async def get_search_summary(
        ctx: Context,
        search_params: SearchParams,
    ):
        """
        Tool to get a comprehensive summary of ALL projects matching search criteria.

        Unlike search_projects (which samples the first 500 results for a quick preview),
        this tool fetches all matching projects to provide accurate, complete statistics.
        Use this when you need exact totals (e.g., "total funding for cancer research").

        Note: This may be slower for large result sets as it pages through all results.

        Args:
            search_params (SearchParams): Search parameters including search term, years, agencies, organizations, pi_name, po_names, and award_types.

        Returns:
            dict: API response containing complete statistics:
            - total_projects: Total number of matching projects
            - year_distribution: Complete breakdown of projects by fiscal year
            - institute_distribution: Complete breakdown by NIH institute/center
            - activity_code_distribution: Complete breakdown by activity code (grant type)
            - organization_distribution: Complete breakdown by institution/organization
            - funding_mechanism_distribution: Complete breakdown by funding mechanism
            - active_status_distribution: Complete breakdown of active vs inactive projects
            - award_amount_stats: Complete funding statistics (total, average, min, max)
        """

        # Get data with fields needed for distributions
        include_fields = [
            IncludeField.PROJECT_NUM.value,
            IncludeField.FISCAL_YEAR.value,
            IncludeField.AGENCY_IC_ADMIN.value,
            IncludeField.ACTIVITY_CODE.value,
            IncludeField.ORGANIZATION.value,
            IncludeField.FUNDING_MECHANISM.value,
            IncludeField.IS_ACTIVE.value,
            IncludeField.AWARD_AMOUNT.value,
        ]

        # Fetch ALL results (pages through entire result set)
        all_results = await get_all_responses(
            search_params,
            include_fields,
        )

        distributions = get_project_distributions(all_results)
        total_projects = len(distributions["project_ids"])

        return {
            "total_projects": total_projects,
            "year_distribution": dict(sorted(distributions["year_distribution"].items(), reverse=True)),
            "institute_distribution": dict(distributions["institute_distribution"].most_common(15)),
            "activity_code_distribution": dict(distributions["activity_code_distribution"].most_common(15)),
            "organization_distribution": dict(distributions["organization_distribution"].most_common(15)),
            "funding_mechanism_distribution": dict(distributions["funding_mechanism_distribution"].most_common()),
            "active_status_distribution": dict(distributions["active_status_distribution"]),
            "award_amount_stats": distributions["award_amount_stats"],
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
            search_params (SearchParams): Search parameters including search term, years, agencies, organizations, pi_name, po_names, and award_types.

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

        distributions = get_project_distributions(all_results)
        project_ids = distributions["project_ids"]

        return {
            "total_projects": total_projects,
            "returned_projects": len(project_ids),
            "project_ids": project_ids,
            "year_distribution": dict(sorted(distributions["year_distribution"].items(), reverse=True)),
            "institute_distribution": dict(distributions["institute_distribution"].most_common(15)),
            "activity_code_distribution": dict(distributions["activity_code_distribution"].most_common(15)),
            "has_more_results": total_projects > len(project_ids),
        }
        
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

        # Convert IncludeField enums to their string values
        field_values = [f.value for f in include_fields]

        # add project_ids to a search_params object
        search_params = SearchParams(
            project_nums=project_ids
        )

        # Call the API
        return await get_all_responses(search_params, field_values)
