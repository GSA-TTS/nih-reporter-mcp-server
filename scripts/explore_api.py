import json 
from api_utils import get_all_responses
from reporter.models import SearchParams, AdvancedTextSearch, ProjectNum
from reporter.utils import get_total_amount

def term_search():

    # set query parameters
    search_params = SearchParams(
        advanced_text_search=AdvancedTextSearch(
            search_text="egf receptor",
            search_field=["projecttitle"],
            operator="all",
        ),
        years=[2016],
    )
    limit = 50 
    include_fields = ["ProjectTitle","FiscalYear","PrincipalInvestigators","ActivityCode","ProjectNum","AgencyIcAdmin","CongDist","AgencyCode","AwardAmount","Organization"]
    
    # get all responses
    response = get_all_responses(search_params, include_fields, limit)

    # export to JSON file 
    with open('tests/test_responses/response.json', 'w') as f:
        json.dump(response, f, indent=4)

term_search()

def funding_by_agency_search():

    # set query parameters
    search_params = SearchParams(
        years=[2018],
        agencies=["NIAID"],
        organizations=["Johns Hopkins University"],
    )
    limit = 500
    include_fields = ["ProjectNum","AwardAmount"]

    # get all responses
    response = get_all_responses(search_params, include_fields, limit)

    # export to JSON file 
    with open('tests/test_responses/org_response.json', 'w') as f:
        json.dump(response, f, indent=4)

    print("Total Award Amount:", get_total_amount(response))

# funding_by_agency_search()

def get_project_details(project_num: str):

    search_params = SearchParams(
        project_nums=[ProjectNum(project_num=project_num)]
    )
    limit = 10 
    include_fields = None 

    response = get_all_responses(search_params, include_fields, limit)

    # export to JSON file 
    with open('tests/test_responses/project_details.json', 'w') as f:
        json.dump(response, f, indent=4)

# get_project_details("1R01MD013338-01")

def get_all_projects():
    
    # set query parameters 
    search_params = SearchParams(
        years=[2018], 
        agencies=["NIMHD"],
    )
    limit = 500
    include_fields = ["ProjectNum","AwardAmount"]

    # get all responses
    response = get_all_responses(search_params, include_fields, limit)
    
    # Export to JSON file
    with open('tests/test_responses/all_projects.json', 'w') as f:
        json.dump(response, f, indent=4)
    
# get_all_projects()
