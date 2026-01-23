def register_prompts(mcp):

    # @mcp.prompt()
    # def project_content_search() -> str:
    #     """Use this prompt to answer questions about the content of NIH-funded research projects."""

    #     return f"""Please help me summarize the content of NIH research grants. Follow these steps:

    #         1. First, use the find_project_ids tool to find grants matching the search parameters
    #         2. Then use the get_project_descriptions tool to get detailed information (including title and abstract)
    #         3. Use this information to answer the user's question."""
    
    @mcp.prompt()
    def project_information_search() -> str:
        """Use this prompt to answer questions about the information of NIH-funded research projects."""

        return f"""Please help me do a summary analysis of NIH research grants. Follow these steps:

            1. Start with search_projects to get the initial count of matching projects                                                                                                                        
            2. Use refine_search to narrow down results by applying filters (years, agencies, activity codes, states)                                                                                          
               - Review the distributions returned to identify useful filters                                                                                                                                  
               - Repeat refinement until the result count is manageable for the query                                                                                                                          
            3. Once satisfied with the scope, use find_project_ids to get the list of project IDs                                                                                                              
            4. Use get_project_information with only the IncludeFields needed to answer the query:                                                                                                             
               - For funding questions: AWARD_AMOUNT, FISCAL_YEAR, DIRECT_COST_AMT, INDIRECT_COST_AMT                                                                                                          
               - For PI questions: PRINCIPAL_INVESTIGATORS, CONTACT_PI_NAME                                                                                                                                    
               - For organization questions: ORGANIZATION, CONG_DIST, ORGANIZATION_TYPE                                                                                                                        
               - For grant type questions: ACTIVITY_CODE, FUNDING_MECHANISM, AGENCY_IC_ADMIN                                                                                                                   
               - Always include PROJECT_NUM for reference                                                                                                                                                      
            5. Use the returned information to answer the user's question.""" 