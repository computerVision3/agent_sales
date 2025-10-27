from pydantic import BaseModel, Field
from typing import TypedDict, List, Dict, Optional
import os
import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import quote
import time
import concurrent.futures
import logging
from functools import partial
from langchain_core.tools import tool

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ------------------------------
# Input and Output Schemas
# ------------------------------
class ScrapeInput(BaseModel):
    path: str = Field(..., description='Path of CSV file')
    max_workers: int = Field(5, description='Maximum concurrent workers (default=5)')
    batch_size: int = Field(50, description='Number of companies to process (default=50)')
    delay: float = Field(1.0, description='Delay between requests in seconds (default=1.0)')

class ScrapeResult(TypedDict):
    path: str
    message: str
    success_count: int
    failed_count: int

# ------------------------------
# Global scraper (singleton)
# ------------------------------
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False},
    delay=10,
    # retries=3
)

# ------------------------------
# Core scraper logic
# ------------------------------
def _search_company(comp_name: str, delay: float = 1.0) -> Optional[Dict]:
    """Search for a company and return its URL if found."""
    try:
        comp_name_url = quote(comp_name)
        search_url = f"https://www.zaubacorp.com/companysearchresults/{comp_name_url}"
        
        response = scraper.get(search_url, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Search failed for {comp_name}: HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table", id="results")
        if not table:
            logger.warning(f"No results table found for {comp_name}")
            return None
        
        rows = table.find_all("tr")
        data_rows = [row for row in rows if len(row.find_all("td")) >= 2]
        if not data_rows:
            logger.warning(f"No data rows found for {comp_name}")
            return None
        
        first_row = data_rows[0]
        tds = first_row.find_all("td")
        link = tds[1].find("a")
        if not link:
            logger.warning(f"No link found for {comp_name}")
            return None
            
        company_name_found = link.text.strip()
        company_url = link.get("href")
        if not company_url.startswith("http"):
            company_url = "https://www.zaubacorp.com" + company_url
        
        return {
            "company_name": company_name_found,
            "company_url": company_url
        }
    except Exception as e:
        logger.error(f"Error searching {comp_name}: {str(e)}")
        return None
    finally:
        time.sleep(delay)

def _scrape_company_directors(company_data: Dict, delay: float = 1.0) -> List[Dict]:
    """Scrape director information from a company page."""
    directors = []
    try:
        response = scraper.get(company_data["company_url"], timeout=15)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch {company_data['company_url']}: HTTP {response.status_code}")
            return directors
        
        company_soup = BeautifulSoup(response.text, "html.parser")
        director_table = None
        
        # Find the directors table
        for t in company_soup.find_all("table"):
            headers = [th.text.strip() for th in t.find_all("th")]
            if "Director Name" in headers:
                director_table = t
                break
        
        if not director_table:
            logger.warning(f"No directors table found for {company_data['company_name']}")
            return directors
        
        # Extract director information
        rows = director_table.find_all("tr")[1:]  # Skip header row
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 3:
                continue
                
            directors.append({
                "Company": company_data["company_name"],
                "DIN": cols[0].text.strip(),
                "Name": cols[1].text.strip(),
                "Designation": cols[2].text.strip()
            })
        
        return directors
    except Exception as e:
        logger.error(f"Error scraping directors for {company_data['company_name']}: {str(e)}")
        return directors
    finally:
        time.sleep(delay)

def _process_company(comp_name: str, delay: float = 1.0) -> List[Dict]:
    """Process a single company: search and scrape directors."""
    company_data = _search_company(comp_name, delay)
    if not company_data:
        return []
    
    return _scrape_company_directors(company_data, delay)

def _scrape_zaubacorp(path: str, max_workers: int = 5, batch_size: int = 50, delay: float = 1.0) -> ScrapeResult:
    """Main scraping function with optimizations."""
    try:
        # Read and prepare company data
        comp_data = pd.read_csv(path)
        if "Title" not in comp_data.columns:
            raise ValueError("CSV must contain a 'Title' column with company names")
            
        comp_data = comp_data.iloc[:, :1]  # Only keep the first column
        full_comp_list = list(comp_data["Title"].dropna().unique())
        
        # Limit to batch_size
        companies_to_process = full_comp_list[:batch_size]
        logger.info(f"Processing {len(companies_to_process)} companies out of {len(full_comp_list)} total")
        
        all_directors = []
        success_count = 0
        failed_count = 0
        
        # Process companies concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            process_func = partial(_process_company, delay=delay)
            future_to_company = {executor.submit(process_func, comp): comp for comp in companies_to_process}
            
            for future in concurrent.futures.as_completed(future_to_company):
                company = future_to_company[future]
                try:
                    directors = future.result()
                    if directors:
                        all_directors.extend(directors)
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Exception processing {company}: {str(e)}")
                    failed_count += 1
                
                # Log progress
                processed = success_count + failed_count
                if processed % 10 == 0 or processed == len(companies_to_process):
                    logger.info(f"Progress: {processed}/{len(companies_to_process)} companies processed")
        
        # Save results
        if all_directors:
            base, ext = os.path.splitext(path)
            # output_path = f"{base}_zauba_enriched{ext}"
            output_path = os.path.join(os.path.dirname(path), f"{base}_zauba_enriched{ext}")
            pd.DataFrame(all_directors).to_csv(output_path, index=False)
            return ScrapeResult(
                path=output_path,
                message=f"CSV generated with {len(all_directors)} director records from {success_count} companies.",
                success_count=success_count,
                failed_count=failed_count
            )
        else:
            return ScrapeResult(
                path="",
                message="No director records found.",
                success_count=0,
                failed_count=len(companies_to_process)
            )
            
    except Exception as e:
        logger.error(f"Fatal error in scraping process: {str(e)}")
        return ScrapeResult(
            path="",
            message=f"Scraping failed: {str(e)}",
            success_count=0,
            failed_count=len(companies_to_process) if 'companies_to_process' in locals() else 0
        )

# ------------------------------
# Async LangGraph tool wrapper
# ------------------------------
@tool("ZaubaCorp-Tool", args_schema=ScrapeInput, return_direct=True)
def scrape_zaubacorp(path: str, max_workers: int = 5, batch_size: int = 50, delay: float = 1.0) -> ScrapeResult:
    """
    Enrich a list of company leads with corporate details from ZaubaCorp.

    This tool reads a CSV containing company names (e.g., exported from Google Maps),
    searches ZaubaCorp for each company, and extracts director and corporate
    information when available.

    Args:
        path (str): Absolute path to a CSV file. The file must include a "Title"
            column with company names.
        max_workers (int): Maximum concurrent workers (default=5)
        batch_size (int): Number of companies to process (default=50)
        delay (float): Delay between requests in seconds (default=1.0)

    Returns:
        ScrapeResult:
            - path (str): Absolute path to the generated CSV file containing
              enriched company and director details (e.g. all_directors.csv).
            - message (str): Summary of the enrichment process, including
              how many records were collected.
            - success_count (int): Number of companies successfully processed
            - failed_count (int): Number of companies that failed to process

    When to use:
        Use this tool to append director and registration details to company
        leads gathered from other sources (such as Google Maps).
    """
    return _scrape_zaubacorp(path, max_workers, batch_size, delay)