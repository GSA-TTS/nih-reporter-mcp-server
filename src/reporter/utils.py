import requests 
import asyncio 
from reporter.models import SearchParams
from fastmcp import Context 

def clean_json(response):
    """
    Cleans JSON response by simplyfing fields with subfields. 

    Args: 
        response (dict): JSON response from the NIH RePORTER API

    Returns: 
        dict: Cleaned JSON response
    """

    # simply JSON response 
    for project in response.get('results', []):
        
        # keep only the organization name and the state
        if project.get('organization'):
            project['org_name'] = project['organization']['org_name']
            project['org_state'] = project['organization']['org_state']
            del project['organization']
        
        # keep only the first part of the agency name
        if project.get('agency_ic_admin'):
            project['agency_ic_admin'] = project['agency_ic_admin']['abbreviation']

        # create list of principal investigators full names
        if project.get('principal_investigators'):
            project['principal_investigators'] = [pi['full_name'] for pi in project['principal_investigators']]

    return response 

def get_total_amount(response):
    """
    Calculates the total award amount from the API response.

    Args:
        response (dict): JSON response from the NIH RePORTER API

    Returns:
        float: Total award amount
    """
    
    if not response or 'results' not in response:
        return 0.0
    
    total_amount = sum(project.get('award_amount', 0) for project in response['results'])
    
    return str(total_amount)

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
    
async def paged_query(search_params:SearchParams, include_fields: list[str], limit=100, offset=0, all_results=None):
    """
    Perform the initial query to get the total number of projects matching the criteria.
    
    Args:
        search_params (SearchParams): Search parameters including years, agencies, organizations, and pi_name.
        limit (int): Number of results to return per request (max 500).
        offset (int): Offset for pagination.
        
    Returns:
        dict: API response containing grant data
    """
    
    payload = {
        "criteria": search_params.to_api_criteria(),
        "offset": offset,
        "limit": limit,
        "include_fields": include_fields,
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }

    response = await search_nih_reporter(payload)
    response = clean_json(response)
    
    total_responses = response['meta']['total']
    
    # if initial call, create empty list to collect results
    if all_results is None:
        all_results = {
            'meta': response['meta'],
            'results': []
        }

    # Collect results from first request
    all_results['results'].extend(response.get('results', []))

    return total_responses, all_results

async def get_initial_response(search_params:SearchParams, include_fields: list[str], limit=100):
    
    offset = 0 
    total_responses, all_results = await paged_query(search_params, include_fields, limit, offset)

    return total_responses, all_results

async def get_all_responses(search_params:SearchParams, include_fields: list[str], limit: int):

    offset = 0 
    total_responses, all_results = await paged_query(search_params, include_fields, limit, offset)

    print(f"Total results: {total_responses}")
    

    # Loop through remaining pages
    while offset + limit < total_responses:
        offset += limit
        print(f"Fetching results {offset} to {offset + limit}...")
        
        total_responses, all_results = await paged_query(search_params, include_fields, limit, offset, all_results)
    
    print(f"Retrieved {len(all_results)} total results")

    return all_results

def get_project_distributions(all_results):
    """
    Calculate distributions of project years, institutes, and activity codes.

    Args:
        all_results (dict): API response containing grant data
    Returns:
        tuple: (project_ids, year_distribution, institute_distribution, activity_code_distribution)
    """

    results = all_results.get("results", [])
        
    # Extract project IDs - handle case where individual results might be strings
    project_ids = []
    for r in results:
        if isinstance(r, dict) and r.get("project_num"):
            project_ids.append({"project_num": r.get("project_num")})
    
    # Calculate distributions
    from collections import Counter
    
    # Year distribution - only process dict results
    year_dist = Counter(
        r.get("fiscal_year") 
        for r in results 
        if isinstance(r, dict) and r.get("fiscal_year")
    )
    
    # Institute/Center distribution
    ic_dist = Counter(
        r.get("agency_ic_admin") 
        for r in results 
        if isinstance(r, dict) and r.get("agency_ic_admin")
    )
    
    # Activity code distribution
    activity_dist = Counter(
        r.get("activity_code") 
        for r in results 
        if isinstance(r, dict) and r.get("activity_code")
    )
    
    return project_ids, year_dist, ic_dist, activity_dist