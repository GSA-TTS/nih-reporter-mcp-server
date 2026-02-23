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

    @mcp.prompt()
    def rcdc_term_frequency(
        institutes: str,
        fiscal_years: str,
        categories: str,
        grant_scope: str = "new_and_continuing",
        activity_codes: str = "",
    ) -> str:
        """Analyze RCDC term frequency across NIH grants for specified institutes, years, and categories.

        Args:
            institutes: Comma-separated NIH institute codes (e.g., "NIMHD" or "NIMHD,NCI").
            fiscal_years: Comma-separated fiscal years (e.g., "2022,2023,2024").
            categories: JSON array of category objects, each with a "name" and "terms" list.
                Example: [{"name": "Cancer", "terms": ["breast cancer", "ovarian cancer"]},
                          {"name": "Respiratory Disease", "terms": ["asthma", "respiratory disease"]}]
            grant_scope: "new_only" for new grants only (award_type 1), or
                "new_and_continuing" for new and competing continuations (award_types 1 and 2).
                Defaults to "new_and_continuing".
            activity_codes: Comma-separated activity codes to restrict analysis
                (e.g., "R01,R21"). Leave empty to include all activity codes.
        """

        if grant_scope == "new_only":
            award_types_label = "new grants only"
            award_types_instruction = 'award_types: ["1"]'
        else:
            award_types_label = "new and competing continuation grants"
            award_types_instruction = 'award_types: ["1", "2"]'

        if activity_codes:
            codes_list = [c.strip() for c in activity_codes.split(",") if c.strip()]
            codes_formatted = "[" + ", ".join(f'"{c}"' for c in codes_list) + "]"
            activity_codes_label = activity_codes
            activity_codes_instruction = f"activity_codes: {codes_formatted}"
        else:
            activity_codes_label = "all"
            activity_codes_instruction = "(omit activity_codes to include all activity codes)"

        return f"""Please perform an RCDC term frequency analysis for NIH grants using these parameters:

**Institutes**: {institutes}
**Fiscal Years**: {fiscal_years}
**Grant Scope**: {award_types_label}
**Activity Codes**: {activity_codes_label}
**Categories**:
{categories}

---

## Step 1: Establish the Baseline Portfolio Count

Call `search_projects` with:
- `agencies`: the institute code(s) above as a list (e.g., ["NIMHD"])
- `years`: the fiscal years above as a list of integers (e.g., [2022, 2023, 2024])
- `{award_types_instruction}`
- `{activity_codes_instruction}`
- No `advanced_text_search`

Record the `total_projects` value — this is your **denominator** for all percentages.

---

## Step 2: Count Projects per Term

For **each term** within **each category**, call `search_projects` with the same baseline
parameters plus:
- `advanced_text_search`:
  - `search_text`: the term (e.g., "breast cancer")
  - `search_field`: ["terms"]  ← searches RCDC/NIH indexed scientific terms specifically
  - `operator`: "and"

Record the `total_projects` count for each term.

---

## Step 3: Get Unduplicated Category Totals

For **each category**, make one additional `search_projects` call combining all of that
category's terms:
- `advanced_text_search`:
  - `search_text`: all terms space-separated (e.g., "breast cancer ovarian cancer")
  - `search_field`: ["terms"]
  - `operator`: "or"  ← returns projects matching ANY term in the category

Record this as the **unduplicated category count** (prevents inflating totals when a single
project matches multiple terms within the same category).

---

## Step 4: Present the Results

Display a Markdown table with one row per term and a summary row per category:

| Category | Term | Grant Count | % of Portfolio |
|----------|------|-------------|----------------|
| Cancer | breast cancer | N | X% |
| Cancer | ovarian cancer | N | X% |
| **Cancer** | ***(all terms, unduplicated)*** | **N** | **X%** |
| Respiratory Disease | asthma | N | X% |
| Respiratory Disease | respiratory disease | N | X% |
| **Respiratory Disease** | ***(all terms, unduplicated)*** | **N** | **X%** |

Include a footer row:
**Total Portfolio (baseline)**: N grants ({institutes}, FY {fiscal_years}, {award_types_label})

---

## Step 5: Summarize Key Takeaways

After the table, write **2–3 concise takeaways** from the data. Consider:
- Which categories or terms show the highest and lowest representation in the portfolio
- Relative proportions across categories (e.g., "Cancer-related terms account for X% of the portfolio, compared to Y% for Respiratory Disease")
- Any notable patterns, concentrations, or gaps worth highlighting for portfolio planning"""
