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

            1. Start with search_projects to get a quick preview of matching projects (samples first 500)
               - Returns total count and distributions (year, institute, activity code, organization, funding mechanism, active status, award stats)
               - Review distributions to understand the data landscape
               - To refine results, call search_projects again with filters added to search_params (years, agencies, activity_codes, states)
               - Repeat until the scope is appropriate for the query

            2. Use get_search_summary when you need accurate, complete statistics (e.g., "total funding for X")
               - Fetches ALL matching projects (not just a 500-result sample)
               - Use this for precise totals, not for exploration
               - May be slower for large result sets

            3. Use find_project_ids to get the list of project IDs for detailed queries
               - Returns up to 500 project IDs matching the search criteria

            4. Use get_project_information with only the IncludeFields needed to answer the query:
               - For funding questions: AWARD_AMOUNT, FISCAL_YEAR, DIRECT_COST_AMT, INDIRECT_COST_AMT
               - For PI questions: PRINCIPAL_INVESTIGATORS, CONTACT_PI_NAME
               - For organization questions: ORGANIZATION, CONG_DIST, ORGANIZATION_TYPE
               - For grant type questions: ACTIVITY_CODE, FUNDING_MECHANISM, AGENCY_IC_ADMIN
               - Always include PROJECT_NUM for reference

            5. Use the returned information to answer the user's question.""" 
