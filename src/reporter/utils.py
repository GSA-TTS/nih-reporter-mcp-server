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
        raise Exception(f"NIH RePORTER API request failed: {e}")
    
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

    if response is None:
        raise Exception("NIH RePORTER API request failed - no response received")

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

async def get_all_responses(search_params:SearchParams, include_fields: list[str], limit=500):

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
    Calculate distributions of project years, institutes, activity codes,
    organizations, funding mechanisms, active status, and award amounts.

    Args:
        all_results (dict): API response containing grant data
    Returns:
        dict: Dictionary containing:
            - project_ids: List of project ID dicts
            - year_distribution: Counter of fiscal years
            - institute_distribution: Counter of NIH institutes/centers
            - activity_code_distribution: Counter of activity codes
            - organization_distribution: Counter of organization names
            - funding_mechanism_distribution: Counter of funding mechanisms
            - active_status_distribution: Counter of active/inactive status
            - award_amount_stats: Dict with total, average, min, max award amounts
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

    # Organization distribution (uses org_name from clean_json)
    org_dist = Counter(
        r.get("org_name")
        for r in results
        if isinstance(r, dict) and r.get("org_name")
    )

    # Funding mechanism distribution
    funding_mech_dist = Counter(
        r.get("funding_mechanism")
        for r in results
        if isinstance(r, dict) and r.get("funding_mechanism")
    )

    # Active status distribution
    active_dist = Counter(
        "Active" if r.get("is_active") else "Inactive"
        for r in results
        if isinstance(r, dict) and r.get("is_active") is not None
    )

    # Award amount statistics
    award_amounts = [
        r.get("award_amount")
        for r in results
        if isinstance(r, dict) and r.get("award_amount") is not None
    ]

    if award_amounts:
        award_stats = {
            "total": sum(award_amounts),
            "average": sum(award_amounts) / len(award_amounts),
            "min": min(award_amounts),
            "max": max(award_amounts),
            "count": len(award_amounts)
        }
    else:
        award_stats = {
            "total": 0,
            "average": 0,
            "min": 0,
            "max": 0,
            "count": 0
        }

    return {
        "project_ids": project_ids,
        "year_distribution": year_dist,
        "institute_distribution": ic_dist,
        "activity_code_distribution": activity_dist,
        "organization_distribution": org_dist,
        "funding_mechanism_distribution": funding_mech_dist,
        "active_status_distribution": active_dist,
        "award_amount_stats": award_stats
    }