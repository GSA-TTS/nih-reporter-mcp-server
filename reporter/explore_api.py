import requests 
import json 

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
    "fiscal_years": [],
    "agencies": [],
    "org_names": [],
    "pi_names": [{"any_name": "Allyson Sgro"}],
}

payload = {
    "criteria": search_criteria,
    "offset": 0,
    "limit": 25,
    "include_fields": ["ProjectTitle","FiscalYear","ContactPiName","ActivityCode","ProjectNum","AgencyIcAdmin","CongDist","AgencyCode","AwardAmount"],
    "sort_field": "project_start_date",
    "sort_order": "desc"
}

response = make_query(payload)
# export to JSON file 
with open('response.json', 'w') as f:
    json.dump(response, f, indent=4)