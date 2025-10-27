from pydantic import BaseModel, Field
from typing import TypedDict
import csv
import os
import asyncio

from langchain_core.tools import tool

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time




class ScrapeInput(BaseModel):
    """
    Input schema for the scraping-tool.

    Attributes:
        keyword (str): Search term to use in Google Maps 
            (e.g., "Company", "Factory", "Industry").
        city (str): The city in which to perform the search.
        max_scrolls (int): Maximum number of times to scroll the results panel.
            Defaults to 5.
    """
    keyword: str = Field(..., description='Search term (e.g., "Company", "Factory", "Industry")')
    city: str = Field(..., description="City to search in")
    max_scrolls: int = Field(5, description="Maximum number of times to scroll the results panel (default=5)")

class ScrapeResult(TypedDict):
    """
    Output schema for the scraping-tool.

    Attributes:
        path (str): Absolute path to the generated CSV file
            containing scraped business data.
        message (str): Human-readable summary of the scraping process,
            including how many records were collected.
    """
    path: str 
    message: str 


def _scrape_maps(keyword: str, city: str, max_scrolls: int = 5) -> ScrapeResult:
    """Blocking Selenium code (wrapped for asyncio.to_thread)."""

    # --- Setup ---
    options = Options()
    # options.add_argument("--headless=new")
    # options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    service = Service("/usr/bin/chromedriver")
    browser = webdriver.Chrome(service=service, options=options)

    search_url = f"https://www.google.com/maps/search/{keyword}+in+{city}"
    browser.get(search_url)
    time.sleep(5)

    # --- Scroll ---
    browser.save_screenshot('debug.png')
    panel = WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@role="feed"]'))
    )

    last_height = 0
    scroll_count = 0
    while scroll_count < max_scrolls:
        browser.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panel)
        time.sleep(2)
        new_height = browser.execute_script("return arguments[0].scrollHeight", panel)
        if new_height == last_height:
            break
        last_height = new_height
        scroll_count += 1

    # --- Collect Place URLs ---
    urls = set()
    places = browser.find_elements(By.XPATH, '//a[contains(@href,"/place/")]')
    for place in places:
        href = place.get_attribute("href")
        if href:
            urls.add(href)
    # --- Scrape Each Place ---
    data_list = []
    for url in urls:
        browser.get(url)
        time.sleep(2)

        # Extract fields
        def get_text(xpath, replace=None):
            try:
                el = browser.find_element(By.XPATH, xpath)
                text = el.text if not replace else el.get_attribute("aria-label").replace(replace, "").strip()  # type: ignore
                return text
            except:
                return "Not available"

        title = get_text('//h1[contains(@class,"DUwDvf")]')
        website = get_text("//a[contains(@aria-label, 'Website:')]")
        address = get_text("//button[contains(@aria-label, 'Address:')]", "Address:")
        phone = get_text("//button[contains(@aria-label, 'Phone:')]", "Phone:")

        data_list.append({
            "Title": title,
            "Website": website,
            "Address": address,
            "Phone": phone,
            "URL": url
        })

    browser.quit()

    # --- Save to CSV ---
    csv_file = f"output/leads_{keyword}_{city}.csv".replace(" ", "_")
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Title", "Website", "Address", "Phone", "URL"])
        writer.writeheader()
        writer.writerows(data_list)

    return ScrapeResult(path= os.path.abspath(csv_file),
            message= f"CSV generated with {len(data_list)} records")


@tool("GoogleMap-Tool", args_schema=ScrapeInput, return_direct=True)
async def Scrape_Maps(keyword: str, city: str, max_scrolls: int = 5) -> ScrapeResult:
    """
    Scrape Google Maps to collect business leads in a given city.

    Usage rules:
      - Always separate the search term (`keyword`) from the location (`city`).
        Example: For "GIDC industry in North Gujarat":
            keyword = "GIDC industry"
            city = "North Gujarat"

      - If `city` is a **region** (e.g., "North Gujarat"):
          * First expand it into specific cities (e.g., ["Mehsana", "Patan", "Palanpur", "Himmatnagar"]).
          * Then call this tool once for each city separately.

      - If `city` is a **single city** (e.g., "Ahmedabad"):
          * Call the tool directly with that city.

    Args:
        keyword (str): Search term (e.g., "Factory", "Metal Scrap", "Industry").
        city (str): City or region name.
        max_scrolls (int): Number of scrolls through the results panel (default=5).

    Returns:
        dict:
            - path (str): Absolute path to the generated CSV file.
            - message (str): Summary of how many records were collected.
    """


    return await asyncio.to_thread(_scrape_maps, keyword, city, max_scrolls)






# from pydantic import BaseModel, Field
# from typing import TypedDict, Optional
# import csv
# import os
# import asyncio
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from functools import partial
# import time
# import random
# import logging

# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# from langchain_core.tools import tool

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# # --- Input & Output Schemas ---
# class ScrapeInput(BaseModel):
#     keyword: str = Field(..., description='Search term (e.g., "Factory", "Metal Scrap")')
#     city: str = Field(..., description="City to search in")
#     max_scrolls: int = Field(5, description="Max scrolls (default=5)")
#     max_workers: int = Field(4, description="Parallel workers (default=4)")
#     timeout: int = Field(30, description="Page load timeout in seconds (default=30)")
#     output_dir: str = Field("./output", description="Output directory for CSV files")

# class ScrapeResult(TypedDict):
#     path: str 
#     message: str 
#     success_count: int
#     failed_count: int

# # --- WebDriver Setup ---
# def _create_driver(timeout: int = 30) -> webdriver.Chrome:
#     options = Options()
#     options.add_argument("--headless=new")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument("--disable-extensions")
#     options.add_argument("--disable-logging")
#     options.add_argument("--disable-plugins")
#     options.add_argument("--disable-images")
#     options.add_argument("--disable-web-security")
#     options.add_argument("--disable-features=VizDisplayCompositor")
#     options.add_argument("--disable-background-timer-throttling")
#     options.add_argument("--disable-renderer-backgrounding")
#     options.add_argument("--disable-blink-features=AutomationControlled")
#     options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     options.add_experimental_option('useAutomationExtension', False)
#     service = Service("/usr/bin/chromedriver")
#     driver = webdriver.Chrome(service=service, options=options)
#     driver.set_page_load_timeout(timeout)
#     return driver

# # --- Safe Text Extraction ---
# def _extract_text_safely(driver: webdriver.Chrome, xpath: str, attribute: str = "text", replace: Optional[str] = None) -> str:
#     try:
#         el = driver.find_element(By.XPATH, xpath)
#         text = el.text if attribute == "text" else el.get_attribute(attribute)
#         if text and replace:
#             text = text.replace(replace, "").strip()
#         return text or "Not available"
#     except (NoSuchElementException, TimeoutException, WebDriverException):
#         return "Not available"

# # --- Scrape a Single Place ---
# def _scrape_place(url: str, timeout: int = 30) -> Optional[dict]:
#     driver = None
#     try:
#         driver = _create_driver(timeout)
#         driver.get(url)
#         time.sleep(random.uniform(1.0, 2.5))
#         WebDriverWait(driver, 10).until(
#             EC.presence_of_element_located((By.CSS_SELECTOR, "h1.DUwDvf"))
#         )
#         title = _extract_text_safely(driver, '//h1[contains(@class,"DUwDvf")]')
#         website = _extract_text_safely(driver, "//a[contains(@aria-label, 'Website')]", "href")
#         address = _extract_text_safely(driver, "//button[contains(@aria-label, 'Address:')]", "aria-label", "Address:")
#         phone = _extract_text_safely(driver, "//button[contains(@aria-label, 'Phone:')]", "aria-label", "Phone:")
#         return {"Title": title, "Website": website, "Address": address, "Phone": phone, "URL": url}
#     except Exception as e:
#         logger.error(f"Error scraping {url}: {str(e)}")
#         return None
#     finally:
#         if driver:
#             driver.quit()

# # --- Main Scraping Function ---
# def _scrape_maps(keyword: str, city: str, max_scrolls: int = 5, max_workers: int = 4, timeout: int = 30, output_dir: str = "./output") -> ScrapeResult:
#     os.makedirs(output_dir, exist_ok=True)
#     driver = None
#     data_list = []
#     success_count = 0
#     failed_count = 0

#     try:
#         driver = _create_driver(timeout)
#         search_url = f"https://www.google.com/maps/search/{keyword}+{city}"
#         driver.get(search_url)
#         panel = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@role="feed"]')))
#         last_height = driver.execute_script("return arguments[0].scrollHeight", panel)

#         for i in range(max_scrolls):
#             driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panel)
#             time.sleep(random.uniform(1.5, 2.5))
#             new_height = driver.execute_script("return arguments[0].scrollHeight", panel)
#             if new_height == last_height:
#                 logger.info(f"No new content after scroll {i+1}, stopping early")
#                 break
#             last_height = new_height

#         urls = set()
#         for place in driver.find_elements(By.XPATH, '//a[contains(@href,"/place/")]'):
#             href = place.get_attribute("href")
#             if href and "/place/" in href:
#                 urls.add(href)
#         logger.info(f"Found {len(urls)} unique URLs")

#         scrape_func = partial(_scrape_place, timeout=timeout)
#         with ThreadPoolExecutor(max_workers=max_workers) as executor:
#             futures = {executor.submit(scrape_func, url): url for url in urls}
#             for future in as_completed(futures):
#                 url = futures[future]
#                 try:
#                     result = future.result()
#                     if result:
#                         data_list.append(result)
#                         success_count += 1
#                     else:
#                         failed_count += 1
#                 except Exception as e:
#                     logger.error(f"Exception processing {url}: {str(e)}")
#                     failed_count += 1
#                 if (success_count + failed_count) % 10 == 0:
#                     logger.info(f"Progress: {success_count + failed_count}/{len(urls)} processed")
#     except Exception as e:
#         logger.error(f"Fatal error in scraping process: {str(e)}")
#     finally:
#         if driver:
#             driver.quit()

#     csv_file = os.path.join(output_dir, f"leads_{keyword}_{city}.csv".replace(" ", "_"))
#     with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=["Title", "Website", "Address", "Phone", "URL"])
#         writer.writeheader()
#         writer.writerows(data_list)

#     return ScrapeResult(
#         path=os.path.abspath(csv_file),
#         message=f"CSV generated with {len(data_list)} records. Success: {success_count}, Failed: {failed_count}",
#         success_count=success_count,
#         failed_count=failed_count
#     )

# # --- Async LangChain Tool ---
# @tool("GoogleMap-Tool", args_schema=ScrapeInput, return_direct=True)
# async def Scrape_Maps(keyword: str, city: str, max_scrolls: int = 5, max_workers: int = 4, timeout: int = 30, output_dir: str = "./output") -> ScrapeResult:
#     """
#     Scrape Google Maps to collect business leads in a given city.

#     Usage rules:
#       - Always separate the search term (`keyword`) from the location (`city`).
#         Example: For "GIDC in North Gujarat":
#             keyword = "GIDC"
#             city = "North Gujarat"

#       - If `city` is a **region** (e.g., "North Gujarat"):
#           * First expand it into specific cities (e.g., ["Mehsana", "Patan", "Palanpur", "Himmatnagar"]).
#           * Then call this tool once for each city separately.

#       - If `city` is a **single city** (e.g., "Ahmedabad"):
#           * Call the tool directly with that city.

#     Args:
#         keyword (str): Search term (e.g., "Factory", "Metal Scrap", "Industry").
#         city (str): City or region name.
#         max_scrolls (int): Number of scrolls through the results panel (default=5).

#     Returns:
#         dict:
#             - path (str): Absolute path to the generated CSV file.
#             - message (str): Summary of how many records were collected.
#     """


#     return await asyncio.to_thread(_scrape_maps, keyword, city, max_scrolls, max_workers, timeout, output_dir)
