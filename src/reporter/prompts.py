def register_prompts(mcp):

    @mcp.prompt()
    def project_content_search() -> str:
        """Use this prompt to answer questions about the content of NIH-funded research projects."""

        return f"""Please help me summarize the content of NIH research grants. Follow these steps:

            1. First, use the find_project_ids tool to find grants matching the search parameters
            2. Then use the get_project_descriptions tool to get detailed information (including title and abstract)
            3. Use this information to answer the user's question."""
    
    @mcp.prompt()
    def project_information_search() -> str:
        """Use this prompt to answer questions about the information of NIH-funded research projects."""

        return f"""Please help me do a summary analysis of NIH research grants. Follow these steps:

            1. First, use the find_project_ids tool to find grants matching the search parameters
            2. Then use the get_project_information tool to get detailed information (including organization, PI, award amount)
            3. Use this information to answer the user's question."""