from fastmcp import FastMCP
import requests 
import asyncio 
from .utils import clean_json, form_search_criteria, get_total_amount
from .models import SearchParams
from starlette.responses import JSONResponse


# Initialize FastMCP server
mcp = FastMCP("reporter",stateless_http=True)

async def search_nih_reporter(payload):
    """
    Search NIH Reporter API for grant information
    
    Args:
        payload (dict): Search criteria
    
    Returns:
        dict: API response containing grant data
    """
    
    # NIH Reporter API endpoint
    url = "https://api.reporter.nih.gov/v2/projects/search"
    
    try:
        # Run the synchronous requests call in a thread pool
        response = await asyncio.to_thread(
            requests.post, 
            url, 
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

@mcp.tool()
async def advanced_term_search(search_params: SearchParams):
    """
    Tool to perform an advanced search of the NIH RePORTER based on a given search term.
    
    Args:
        search_params (SearchParams): Search parameters including search term, years, agencies, organizations, and pi_name.
    Returns:
        dict: API response containing grant data
    """

    payload = {
        "criteria": search_params.to_api_criteria(),
        "offset": 0,
        "limit": 25,
        "include_fields": ["ProjectTitle","FiscalYear","PrincipalInvestigators","ActivityCode","ProjectNum","AgencyIcAdmin","CongDist","AgencyCode","AwardAmount","Organization"],
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }
    
    response = await search_nih_reporter(payload)

    return clean_json(response)

@mcp.tool()
async def funding_by_organization(organizations: list[str] | None = None,
                               years: list[int] | None = None, 
                               agencies: list[str] | None = None,
                               ):
    """
        Tool to get amount of funding by organization for a given year (or years) and agency (or agencies)
        
        Args:
            organization (string): the organization (or organizations) that is (are) the primary recipient(s) of the grant (e.g. "Boston University")
            years (list): List of fiscal years where projects are active (e.g. [2023, 2024])
            agencies (list[string]): the agency providing funding for the grant (default is "NIH").
                Each agency is represented by a code and multiple agencies can be specified (e.g. ["NIMHD", "NIAID"]). 
                Valid agency codes include:
                    Clinical Center - CLC
                    Center for Scientific Review - CSR
                    Center for Information Technology - CIT
                    John E. Fogarty International Center - FIC
                    National Center for Advancing Translational Sciences - NCATS
                    National Center for Complementary and Integrative Health- NCCIH
                    National Cancer Institute - NCI
                    National Center for Research Resources - NCRR
                    National Eye Institute - NEI
                    National Human Genome Research Institute - NHGRI
                    National Heart, Lung, and Blood Institute - NHLBI
                    National Institute on Aging - NIA
                    National Institute on Alcohol Abuse and Alcoholism - NIAAA
                    National Institute of Allergy and Infectious Diseases - NIAID
                    National Institute of Arthritis and Musculoskeletaland Skin Diseases - NIAMS
                    National Institute of Biomedical Imaging and Bioengineering - NIBIB
                    Eunice Kennedy Shriver National Institute of Child Health and Human Development - NICHD
                    National Institute on Drug Abuse - NIDA
                    National Institute on Deafness and Other Communication Disorders - NIDCD
                    National Institute of Dental and Craniofacial Research - NIDCR
                    National Institute of Diabetes and Digestive and Kidney Diseases - NIDDK
                    National Institute of Environmental Health Sciences - NIEHS
                    National Institute of General Medical Sciences - NIGMS
                    National Institute of Mental Health - NIMH
                    National Institute on Minority Health and Health Disparities - NIMHD
                    National Institute of Neurological Disorders and Stroke - NINDS
                    National Institute of Nursing Research - NINR
                    National Library of Medicine - NLM
                    Office of the Director - OD
            
        Returns:
            dict: API response containing grant data
        """
    
    search_criteria = form_search_criteria(
        agencies=agencies, 
        years=years,
        organizations=organizations, 
    )

    payload = {
        "criteria": search_criteria,
        "offset": 0,
        "limit": 500,
        "include_fields": ["AwardAmount"],
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }

    response = await search_nih_reporter(payload)

    return get_total_amount(response)

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


