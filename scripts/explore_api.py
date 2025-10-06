import requests 
import json 
from reporter.utils import clean_json, form_search_criteria, get_total_amount
from reporter.models import SearchParams, AdvancedTextSearch

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

term_search()
