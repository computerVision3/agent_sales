import sys
import logging
import asyncio
import pandas as pd
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from ddgs import DDGS
import time


# ------------------ LOGGING CONFIG ------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)
logger = logging.getLogger("LinkedInSearchTool")


# ------------------ INPUT MODEL ------------------
class SearchInput(BaseModel):
    profession: str = Field(..., description="Job title or profession to search for on LinkedIn.")
    company: Optional[str] = Field(None, description="Company name to search for on LinkedIn.")
    csv_file: Optional[str] = Field(None, description="Path to CSV file with a 'company' column.")
    save_csv: Optional[bool] = Field(False, description="If True, save results to output/linkedin_results.csv.")


# ------------------ CORE FUNCTION ------------------
def _linkedin_search(search_input: SearchInput) -> Dict[str, List[Dict[str, str]]]:
    base_prefix = "site:in.linkedin.com/in"
    queries = []

    profession = search_input.profession.strip()
    if not profession:
        raise ValueError("Profession cannot be empty.")

    # Build queries
    if search_input.company:
        queries.append(f'"{profession}" AND "{search_input.company.strip()}" {base_prefix} ')

    elif search_input.csv_file:
        df = pd.read_csv(search_input.csv_file)
        if "company" not in df.columns:
            raise ValueError("CSV must have a 'company' column.")
        for company in df["company"].dropna().astype(str):
            queries.append(f'"{profession}" AND "{company.strip()}" {base_prefix} ')

    else:
        raise ValueError("Either 'company' or 'csv_file' must be provided.")

    # Perform search
    results: Dict[str, List[Dict[str, str]]] = {}
    with DDGS() as ddgs:
        DDGS.threads = 3
        for q in queries:
            logger.info(f"Searching LinkedIn for: {q}")
            try:
                items = list(ddgs.text(q, max_results=3, region="in-en", safesearch="off", backend="duckduckgo"))
                formatted = [
                    {"title": r.get("title", ""), "link": r.get("href", "")}
                    for r in items if r.get("href")
                ]
                results[q] = formatted
                logger.info(f"Found {len(formatted)} results for: {q}")
                time.sleep(2)  # avoid rate limiting
            except Exception as e:
                logger.error(f"Error searching for '{q}': {e}")
                results[q] = [{"title": "Error", "link": str(e)}]

    # Optionally save to CSV
    if search_input.save_csv and results:
        output_path = "output/linkedin_results.csv"
        rows = []
        for query, items in results.items():
            for item in items:
                rows.append({"query": query, "title": item["title"], "link": item["link"]})
        pd.DataFrame(rows).to_csv(output_path, index=False)
        logger.info(f"Results saved to: {output_path}")

    return results


# ------------------ LANGCHAIN TOOL WRAPPER ------------------
@tool("LinkedinSearch-Tool", args_schema=SearchInput, return_direct=True)
async def linkedin_tool(
    profession: str,
    company: Optional[str] = None,
    csv_file: Optional[str] = None,
    save_csv: Optional[bool] = False,
    ) -> Dict[str, List[Dict[str, str]]]:    
    """
    Scrape professional profiles from LinkedIn using DuckDuckGo search.

    Each query automatically follows this pattern:
        site:in.linkedin.com/in "PROFESSION" AND "COMPANY"

    Usage rules:
      - 'profession' is always required.
      - You can provide either:
          * A single company (via `company`), OR
          * A CSV file with a 'company' column for multiple searches.

    Examples:
        1. Single Query:
            profession = "DIRECTOR"
            company = "SURAJ FORWARDERS"

            → Actual search:
              site:in.linkedin.com/in "DIRECTOR" AND "SURAJ FORWARDERS"

        2. Batch Mode (CSV):
            CSV file example (companies.csv):
                company
                Microsoft
                Amazon
                Meta

            profession = "HR Manager"

            → The tool will search for:
                - site:in.linkedin.com/in "HR Manager" AND "Microsoft"
                - site:in.linkedin.com/in "HR Manager" AND "Amazon"
                - site:in.linkedin.com/in "HR Manager" AND "Meta"

    Args:
        input_data (SearchInput):
            - profession (str): Job title (e.g., "DIRECTOR") — required.
            - company (str, optional): Company name (e.g., "SURAJ FORWARDERS").
            - csv_file (str, optional): Path to CSV with a 'company' column.

    Returns:
        dict[str, list[dict[str, str]]]:
            Mapping of each constructed LinkedIn query to its list of search results:
                - title (str): Result title.
                - link (str): LinkedIn profile URL.
    """
    input_data = SearchInput(
    profession=profession,
    company=company,
    csv_file=csv_file,
    save_csv=save_csv,
    )
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _linkedin_search, input_data)
