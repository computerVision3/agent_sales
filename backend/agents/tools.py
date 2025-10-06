from agents.config import llm

from tools.map_scrapper import Scrape_Maps
from tools.data_analyzer import DataAnalyst
from tools.zauba_corp import scrape_zaubacorp
from tools.web_search import Web_Search
from tools.url_scraper import scrape_website



def model_with_tools():
    """
    Bind the pre-configured LLM with the default tools directly.
    """
    tools = [Scrape_Maps, DataAnalyst, scrape_zaubacorp, scrape_website, Web_Search]

    model = llm()
    model = model.bind_tools(tools)
    print(f"Model loaded with tools: {[tool.name for tool in tools]}")
    return tools, model
