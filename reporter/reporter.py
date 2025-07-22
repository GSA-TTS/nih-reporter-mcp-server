import httpx
from mcp.server.fastmcp import FastMCP
import requests 
import asyncio 

# Initialize FastMCP server
mcp = FastMCP("reporter")

async def search_nih_reporter(payload):
    """
    Search NIH Reporter API for grant information
    
    Args:
        criteria (dict): Search criteria
        offset (int): Starting position for results
        limit (int): Number of results to return (max 500)
    
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
async def advanced_term_search(search_term: str):
    """
    Tool to perform an advanced search of the NIH RePORTER based on a given search term.
    
    Args:
        term (string): term to search for in the NIH RePORTER database.
        
    
    Returns:
        dict: API response containing grant data
    """
    
    search_criteria = {
            "advanced_text_search": {
                "operator": "advanced",
                "search_field": "terms",
                "search_text": search_term
            },
            "fiscal_years": [2023, 2024],
            "agencies": ["NIH"]
    }

    payload = {
        "criteria": search_criteria,
        "offset": 0,
        "limit": 25,
        "include_fields": ["ApplId","SubprojectId","FiscalYear","OrgName","OrgCity", "OrgState","OrgStateName","DeptType", "ProjectNum","OrgCountry"],
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }
    
    return await search_nih_reporter(payload)


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')