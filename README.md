# NIH RePORTER MCP Server 

⚠️ DISCLAIMER: This is a proof of concept and is not intended for production use.

## 📖 Overview 

This project is a pilot study for the creation of an MCP server for the NIH's grant database: RePORTER. The server contains three tools, which vary in amount of detail. In order from broadest to deepest: 

- **get_all_projects_by_ic**: performs a basic search to get all projects associated with search criteria (such as all projects from a given institute in a given year or all projects to a given state or specific research organization). 
- **project_text_search**: performs a text search to find projects relevant to a topic area or methodology. 
- **get_project_details**: performs a search to get all project details for a small number (less than 10) projects by their project ID. 

Each tool is registered with the MCP server and can be called by an LLM or other MCP client. 

## 🚀 Quick Start 

The code as written is intended for cloud deployment. Contact the admins if you are interested in testing the cloud deployment. Otherwise, the repository may be forked and modified for local implementation. 

## 📐 Project Structure 

- src/reporter/ - Main package code 
- scripts/ - Scripts used for querying the API outside of the MCP server 

## 📚 Resources

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/docs/getting-started/intro)
- [FastMCP Documentation](https://gofastmcp.com/getting-started/welcome)
- [NIH RePORTER API Documentation](https://api.reporter.nih.gov/)

## 💬 Contact

For any questions please contact [Mark Aronson](mailto:mark.aronson@gsa.gov)
