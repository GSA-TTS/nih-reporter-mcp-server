import requests 
import json 
from reporter.utils import clean_json, form_search_criteria, get_total_amount
from reporter.models import SearchParams, AdvancedTextSearch, ProjectNum

def make_query(payload):

    # NIH Reporter API endpoint
    url = "https://api.reporter.nih.gov/v2/projects/search"
    
    try:
        # Run the synchronous requests call in a thread pool
        response = requests.post(
            url, 
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()  # Raise an exception for bad status codes
        
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}")
        return None

def term_search():

    search_params = SearchParams(
        advanced_text_search=AdvancedTextSearch(
            search_text="egf receptor cell migration",
            search_field=["projecttitle","terms"],
            operator="or",
        ),
        years=[2016]
    )

    params_dict = search_params.to_api_criteria()

    print(params_dict)

    payload = {
        "criteria": params_dict,
        "offset": 0,
        "limit": 50,
        "include_fields": ["ProjectTitle","FiscalYear","PrincipalInvestigators","ActivityCode","ProjectNum","AgencyIcAdmin","CongDist","AgencyCode","AwardAmount","Organization"],
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }

    response = make_query(payload)

    response = clean_json(response)

    # export to JSON file 
    with open('tests/test_responses/response.json', 'w') as f:
        json.dump(response, f, indent=4)

def funding_by_agency_search():

    search_criteria = form_search_criteria(
        years=[2018],
        agencies=["NIAID"],
        organizations=["Johns Hopkins University"],
    )

    payload = {
        "criteria": search_criteria,
        "offset": 0,
        "limit": 500,
        "include_fields": ["ProjectNum","AwardAmount"],
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }

    response = make_query(payload)

    # export to JSON file 
    with open('test_responses/search_response.json', 'w') as f:
        json.dump(response, f, indent=4)

    print("Total Award Amount:", get_total_amount(response))

# term_search()

def get_project_details(project_num: ProjectNum):

    payload = {
        "criteria": {
            "project_nums": [project_num]
        },
        "offset": 0,
        "limit": 10,
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }

    response = make_query(payload)

    # export to JSON file 
    with open('tests/test_responses/project_details.json', 'w') as f:
        json.dump(response, f, indent=4)

# get_project_details("1F32DK109635-01A1")

def get_all_projects():
    search_params = SearchParams(
        years=[2016], 
        agencies=["NIMHD"],
    )

    params_dict = search_params.to_api_criteria()

    print(params_dict)

    limit = 500
    offset = 0
    all_results = []
    
    # Make initial request to get total count
    payload = {
        "criteria": params_dict,
        "offset": offset,
        "limit": limit,
        "include_fields": ["ProjectTitle", "FiscalYear", "ProjectNum", "AgencyIcAdmin", "Organization"],
        "sort_field": "project_start_date",
        "sort_order": "desc"
    }

    response = make_query(payload)
    response = clean_json(response)
    
    total_responses = response['meta']['total']
    print(f"Total results: {total_responses}")
    
    # Collect results from first request
    all_results.extend(response.get('results', []))
    
    # Loop through remaining pages
    while offset + limit < total_responses:
        offset += limit
        print(f"Fetching results {offset} to {offset + limit}...")
        
        payload["offset"] = offset
        
        response = make_query(payload)
        response = clean_json(response)
        
        all_results.extend(response.get('results', []))
    
    print(f"Retrieved {len(all_results)} total results")
    
    # Combine all results into final response structure
    final_response = {
        'meta': {
            'total': total_responses,
            'offset': 0,
            'limit': len(all_results)
        },
        'results': all_results
    }
    
    # Export to JSON file
    with open('tests/test_responses/all_projects.json', 'w') as f:
        json.dump(final_response, f, indent=4)
    
    return final_response

get_all_projects()
