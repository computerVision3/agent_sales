from langchain_core.prompts import ChatPromptTemplate

from agents.config import llm

from tools.web_scrapper import scrape_maps
from tools.data_analyzer import DataAnalyst
from tools.zauba_corp import scrape_zaubacorp



def model_with_tools():
    """
    Bind the pre-configured LLM with the default tools directly.
    """
    tools = [scrape_maps, DataAnalyst, scrape_zaubacorp]
    model = llm()
    model = model.bind_tools(tools)

    return tools, model
