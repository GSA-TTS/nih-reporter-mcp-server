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
        
        # keep only the first part of the organization name
        if project.get('organization'):
            project['organization'] = project['organization']['org_name']
        
        # keep only the first part of the agency name
        if project.get('agency_ic_admin'):
            project['agency_ic_admin'] = project['agency_ic_admin']['abbreviation']

        # create list of principal investigators full names
        if project.get('principal_investigators'):
            project['principal_investigators'] = [pi['full_name'] for pi in project['principal_investigators']]

    return response 

def form_search_criteria(search_term=None, years=None, agencies=None, organizations=None, pi_name=None):
    """
    Forms search criteria for NIH RePORTER API based on provided parameters.
    """

    search_criteria = {}

    # Set search criteria based on provided parameters
    if search_term:
        search_criteria["advanced_text_search"] = {
            "operator": "advanced",
            "search_field": "terms",
            "search_text": search_term
        }
    if years:
        search_criteria["fiscal_years"] = years
    if agencies:
        search_criteria["agencies"] = agencies
    if organizations:
        search_criteria["org_names"] = organizations
    if pi_name:
        search_criteria["pi_names"] = [{"any_name": pi_name}]
    
    return search_criteria