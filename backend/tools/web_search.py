from pydantic import BaseModel, Field
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import asyncio

# Initialize the DuckDuckGo search runner
search_runner = DuckDuckGoSearchRun()

class SearchInput(BaseModel):
    """
    Input schema for the web search tool.
    
    Attributes:
        query (str): The search query string for performing a web search.
    """
    query: str = Field(..., description="The query string to search on the web")

class SearchOutput(BaseModel):
    """
    Output schema for the web search tool.
    
    Attributes:
        message (str): The search results as a string.
    """
    message: str

async def _web_search(query: str) -> SearchOutput:
    """
    Perform an asynchronous web search using DuckDuckGo.

    Args:
        query (str): The search query to execute.

    Returns:
        SearchOutput: The search results wrapped in a Pydantic model.
    """
    # DuckDuckGoSearchRun is synchronous, so run it in a thread pool to avoid blocking
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, search_runner.invoke, query)
    return SearchOutput(message=result)

@tool("WebSearch-Tool", args_schema=SearchInput, return_direct=True)
async def Web_Search(query: str) -> SearchOutput:
    """
    Execute a web search for a specific query and return the results.

    This tool uses DuckDuckGo to fetch search results asynchronously.
    
    Args:
        query (str): The query string to search.

    Returns:
        SearchOutput: The results of the search.
    """
    # Simply await the async _web_search function
    return await _web_search(query)
