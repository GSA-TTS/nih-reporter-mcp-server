import requests 
import json 
import pandas as pd 
from utils import clean_json, form_search_criteria, get_total_amount

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

    search_criteria = form_search_criteria(
        search_term="",
        years=[2018],
        agencies=["NIAID"],
        organizations=["Johns Hopkins University"],
        pi_name=""
    )

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

    # # convert json into a dataframe 
    # df = pd.json_normalize(response['results'])

    # # sum award amount 
    # total_funding = df['award_amount'].sum()

    # # add total funding to the dataframe
    # df = df._append({'project_num': 'Total Funding', 'award_amount': total_funding}, ignore_index=True)

    # # export to CSV file
    # df.to_csv('test_responses/search_response.csv', index=False)

funding_by_agency_search()
