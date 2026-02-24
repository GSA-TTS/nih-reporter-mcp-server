def register_prompts(mcp):

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

    @mcp.prompt()
    def rcdc_term_frequency(
        rcdc_terms: str,
        fiscal_years: str,
        institutes: str = "",
    ) -> str:
        """Plot the number of NIH grants matching one or more RCDC terms across fiscal years.

        Args:
            rcdc_terms: Comma-separated RCDC terms to search for (e.g., "breast cancer,ovarian cancer").
            fiscal_years: Comma-separated fiscal years (e.g., "2020,2021,2022,2023,2024").
            institutes: Comma-separated NIH institute codes to filter by (e.g., "NCI,NIMHD").
                Leave empty to search across all institutes.
        """

        terms_list = [t.strip() for t in rcdc_terms.split(",") if t.strip()]
        years_list = [y.strip() for y in fiscal_years.split(",") if y.strip()]

        if institutes:
            institute_list = [i.strip() for i in institutes.split(",") if i.strip()]
            institutes_label = institutes
            agencies_instruction = f"- `agencies`: {institute_list}"
        else:
            institutes_label = "all institutes"
            agencies_instruction = "- (omit `agencies` to search all institutes)"

        terms_bullet_list = "\n".join(f'  - "{t}"' for t in terms_list)

        return f"""Plot the number of NIH grants for each RCDC term by fiscal year.

            **RCDC Terms**: {rcdc_terms}
            **Fiscal Years**: {fiscal_years}
            **Institutes**: {institutes_label}

            ---

            ## Step 1: Fetch grant counts per term

            For **each term** listed below, call `get_search_summary` with:
            {agencies_instruction}
            - `years`: [{", ".join(years_list)}]
            - `advanced_text_search`:
            - `search_text`: <the term>
            - `search_field`: ["terms"]
            - `operator`: "and"

            Terms to search:
            {terms_bullet_list}

            Each response includes a `year_distribution` with the grant count per fiscal year for that term.

            ---

            ## Step 2: Plot the results

            Use Python (matplotlib or similar) to produce a line chart with one line per term:
            - X-axis: fiscal year
            - Y-axis: number of grants
            - One labeled line per term
            - Title: 'NIH Grant Counts by RCDC Term and Fiscal Year ({institutes_label})'

            Also display the raw counts in a table:

            | Fiscal Year | {" | ".join(terms_list)} |
            |-------------|{"---|" * len(terms_list)}
            | YYYY        | {"N | " * len(terms_list)}"""

    @mcp.prompt()
    def activity_code_stacked_bar(
        fiscal_years: str,
        institutes: str = "",
        search_term: str = "",
    ) -> str:
        """Plot a stacked bar chart of NIH grant counts by activity code over fiscal years.

        Args:
            fiscal_years: Comma-separated fiscal years (e.g., "2020,2021,2022,2023,2024").
            institutes: Comma-separated NIH institute codes to filter by (e.g., "NCI,NIMHD").
                Leave empty to search across all institutes.
            search_term: Optional RCDC term to restrict grants to a research area (e.g., "breast cancer").
                Leave empty to include all grants.
        """

        years_list = [y.strip() for y in fiscal_years.split(",") if y.strip()]

        if institutes:
            institute_list = [i.strip() for i in institutes.split(",") if i.strip()]
            institutes_label = institutes
            agencies_instruction = f"- `agencies`: {institute_list}"
        else:
            institutes_label = "all institutes"
            agencies_instruction = "- (omit `agencies` to search all institutes)"

        if search_term:
            search_term_label = f'"{search_term}"'
            search_term_instruction = f"""- `advanced_text_search`:
  - `search_text`: "{search_term}"
  - `search_field`: ["terms"]
  - `operator`: "and\""""
        else:
            search_term_label = "all grants"
            search_term_instruction = "- (omit `advanced_text_search` to include all grants)"

        return f"""Plot a stacked bar chart of NIH grant counts by activity code for each fiscal year.

**Fiscal Years**: {fiscal_years}
**Institutes**: {institutes_label}
**Search Term**: {search_term_label}

---

## Step 1: Fetch the cross-tabulation

Call `get_activity_by_year` once with:
{agencies_instruction}
- `years`: [{", ".join(years_list)}]
{search_term_instruction}

The response is a nested dict of `{{year: {{activity_code: count}}}}` covering all requested years.

---

## Step 2: Plot the results

Use Python (matplotlib or similar) to produce a stacked bar chart:
- X-axis: fiscal year
- Y-axis: number of grants
- Each bar stacked by activity code
- Legend identifying each activity code
- Title: 'NIH Grant Counts by Activity Code ({institutes_label})'

Also display the raw counts in a table with one column per activity code:

| Fiscal Year | R01 | R21 | ... |
|-------------|-----|-----|-----|
| YYYY        | N   | N   | ... |"""
