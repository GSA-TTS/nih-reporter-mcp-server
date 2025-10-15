from fastmcp import Context
from reporter.models import SearchParams
from reporter.utils import get_all_responses, get_initial_response, elicit_refined_search


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
    include_fields = ["ProjectTitle","FiscalYear","PrincipalInvestigators","ActivityCode","ProjectNum","AgencyIcAdmin","CongDist","AgencyCode","AwardAmount","Organization"]

    # Allow up to 3 refinement attempts
    refinement_attempts = 0
    max_attempts = 3

    # make the initial search 
    total, response = await get_initial_response(search_params, include_fields, limit)

    while total > 100 and refinement_attempts < max_attempts:
        refined_term = await elicit_refined_search(ctx, total)
    
        if refined_term in ["Search cancelled", "Information not provided"]:
            return {"error": refined_term, "total_results": total}
    
        # Update search with refined term
        search_params.advanced_text_search.search_text = refined_term
        total, response = await get_initial_response(search_params, include_fields, limit)
        refinement_attempts += 1

    if total > 100:
        return {
            "error": f"Search still returns {total} results after {max_attempts} refinements. Please provide more specific criteria.",
            "total_results": total
        }

    # if total > 100:
    #     return {"error: too many results. Ask the user to refine their search and base provide suggestions for narrower keywords based on the initial search results."}

    # Call the API 
    return await get_all_responses(search_params, include_fields, limit)

async def elicit_refined_search(
        ctx: Context,
        total: int
    ) -> str:

        result = await ctx.elicit(
            message = f"The search returned {total} results (maximum 100). Please provide more specific keywords or criteria to narrow down the search.",
            response_type = str    
        )

        if result.action == "accept":
            return result.data 
        elif result.action == "decline":
            return "Information not provided"
        else: # cancel
            return "Search cancelled" 