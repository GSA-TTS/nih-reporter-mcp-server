import requests 
import json 
from utils import clean_json

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

search_criteria = {
    "advanced_text_search": {
        "operator": "advanced",
        "search_field": "terms",
        "search_text": ""
    },
    "fiscal_years": [2024],
    "agencies": [""],
    "org_names": ["University of California, San Francisco"],
    "pi_names": [{"any_name": ""}],
}

payload = {
    "criteria": search_criteria,
    "offset": 0,
    "limit": 500,
    "include_fields": ["ProjectTitle","FiscalYear","PrincipalInvestigators","ActivityCode","ProjectNum","AgencyIcAdmin","CongDist","AgencyCode","AwardAmount","Organization"],
    "sort_field": "project_start_date",
    "sort_order": "desc"
}

response = make_query(payload)

response = clean_json(response)

# export to JSON file 
with open('response.json', 'w') as f:
    json.dump(response, f, indent=4)