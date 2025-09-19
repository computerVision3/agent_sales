import pandas as pd
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import quote
import time
import os

def scrape_zaubacorp(path: str):
    """
    Scrape Zaubacorp exactly like your notebook approach.
    Expects a CSV with a column 'Title' containing company names.
    Saves results as 'all_directors.csv' in the same directory as input.
    """

    # 1. Load companies
    comp_data = pd.read_csv(path)
    comp_data = comp_data.iloc[:, :1]  # Only first column
    full_comp_list = list(comp_data["Title"])
    print(f"Loaded {len(full_comp_list)} companies.")

    # 2. Setup scraper
    scraper = cloudscraper.create_scraper()
    all_directors = []

    # 3. Loop through companies
    for comp_name in full_comp_list[:50]:  # Adjust range as needed
        try:
            print(f"\nSearching for: {comp_name}")
            comp_name_url = quote(comp_name)
            search_url = f"https://www.zaubacorp.com/companysearchresults/{comp_name_url}"

            response = scraper.get(search_url)
            print(f"Search URL status: {response.status_code}")
            soup = BeautifulSoup(response.text, "html.parser")

            table = soup.find("table", id="results")
            if not table:
                print(f"No results table found for {comp_name}")
                continue

            rows = table.find_all("tr")
            data_rows = [row for row in rows if len(row.find_all("td")) >= 2]
            if not data_rows:
                print(f"No data rows found for {comp_name}")
                continue

            # Use first result
            first_row = data_rows[0]
            tds = first_row.find_all("td")
            link = tds[1].find("a")
            company_name_found = link.text.strip()
            company_url = link.get("href")
            if not company_url.startswith("http"):
                company_url = "https://www.zaubacorp.com" + company_url

            print(f"Fetching directors for: {company_name_found} -> {company_url}")

            response = scraper.get(company_url)
            print(f"Company page status: {response.status_code}")
            company_soup = BeautifulSoup(response.text, "html.parser")

            # Find table containing "Director Name"
            director_table = None
            tables = company_soup.find_all("table")
            for t in tables:
                headers = [th.text.strip() for th in t.find_all("th")]
                if "Director Name" in headers:
                    director_table = t
                    break

            if director_table:
                rows = director_table.find_all("tr")[1:]  # Skip header
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) < 3:
                        continue
                    all_directors.append({
                        "Company": company_name_found,
                        "DIN": cols[0].text.strip(),
                        "Name": cols[1].text.strip(),
                        "Designation": cols[2].text.strip()
                    })
                print(f"Found {len(rows)} directors for {company_name_found}")
            else:
                print(f"No directors table found for {company_name_found}")

            time.sleep(1)

        except Exception as e:
            print(f"Error processing {comp_name}: {e}")

    # 4. Save results
    if all_directors:
        output_path = os.path.join(os.path.dirname(path), "all_directors.csv")
        df = pd.DataFrame(all_directors)
        df.to_csv(output_path, index=False)
        print(f"\nSaved {len(all_directors)} director records to {output_path}")
    else:
        print("\nNo director records found.")

# ------------------------------
# Run script
# ------------------------------
if __name__ == "__main__":
    input_csv_path = "/home/ai/agent_sales/leads_GIDC_factory_Ahmedabad.csv"  # Change path as needed
    scrape_zaubacorp(input_csv_path)
