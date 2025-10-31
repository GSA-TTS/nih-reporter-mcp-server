def register_prompts(mcp):

    @mcp.prompt()
    def research_topic_deep_dive(topic: str, num_grants: int = 30) -> str:
        """Search for NIH grants on a specific topic and get detailed information about the most relevant ones"""

        return f"""Please help me research NIH grants about {topic}. Follow these steps:

            1. First, use the project_text_search tool to find grants related to "{topic}"
            2. Review the search results and identify the {num_grants} most relevant grants based on:
            - Relevance to the topic
            - Funding amount
            - Recent activity
            3. For each of those {num_grants} grants, use the get_project_details tool with the project number to get comprehensive details
            4. Summarize the key findings, including:
            - Common research themes and approaches
            - Funding trends and amounts
            - Notable researchers and institutions
            - Geographic distribution

            Focus on recent grants (last 3-5 years) unless I specify otherwise."""