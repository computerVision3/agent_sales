import pandas as pd
import asyncio
from pydantic import BaseModel, Field
from typing import TypedDict, Optional, List
from langchain_core.tools import tool
from langchain.agents.agent_types import AgentType
from langchain_ollama import ChatOllama
from langchain_experimental.agents import create_pandas_dataframe_agent
from agents.config import llm
from langchain_experimental.tools import PythonAstREPLTool

class DataAnalystInput(BaseModel):
    """
    Input schema for the DataAnalyst tool.

    Attributes:
        path (str): Absolute path to the CSV file to analyze.
        query (Optional[str]): Natural language question or instruction
            to analyze the data (e.g., "Summarize top 10 companies by revenue").
    """
    path: str = Field(..., description="Absolute path to the CSV file to analyze")
    query: Optional[str] = Field(None, description="Natural language query or instruction for analysis")


class DataAnalystResult(TypedDict):
    """
    Output schema for the DataAnalyst tool.

    Attributes:
        query (Optional[str]): The query that was analyzed.
        path (str): Absolute path of the CSV file analyzed.
        response (str): LLM-generated response based on the CSV data.
        records (int): Number of rows in the CSV file.
        columns (list[str]): List of column names in the CSV file.
    """

    path: str
    query: Optional[str]
    response: str
    records: int
    columns: List[str]



@tool("data_analyst-tool", args_schema=DataAnalystInput, return_direct=True)
async def DataAnalyst(path: str, query: Optional[str] = None, llm_instance = None) -> DataAnalystResult:
    """
    Analyze a CSV file and provide insights using a pandas DataFrame agent.

    Args:
        path (str): Absolute path to the CSV file to analyze.
        query (Optional[str]): Natural language question or instruction 
            (e.g., "Summarize top 10 companies", 
            "Which company has the highest number of directors?").

        llm (ChatOllama, optional): The LLM instance to use. Defaults to the global llm.

    Returns:
        dict:
            - path (str): Absolute path of the analyzed CSV file.
            - query (str | None): The user’s query.
            - response (str): LLM-generated answer based on the CSV data.
            - records (int): Number of rows in the CSV file.
            - columns (list[str]): List of column names in the CSV file.

    When to use:
        Use this tool when you need to explore or summarize structured data 
        from a CSV file — for example, after scraping leads or enriching 
        company details. It supports natural language queries that get 
        translated into pandas operations.
    """
    my_df = await asyncio.to_thread(pd.read_csv, path)
    
    if llm_instance is None:
        llm_instance = llm()

    python_tool = PythonAstREPLTool()

    agent = create_pandas_dataframe_agent(
        llm=llm_instance, 
        df=my_df,
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        allow_dangerous_code=True,
        verbose=True,
        extra_tools=[python_tool]
    )
    agent.handle_parsing_errors = True 
    response = await asyncio.to_thread(agent.invoke, {"input": query}) # type: ignore
    # response = await agent.ainvoke({"input": query})
    raw_output = response.get("output", response)
    return DataAnalystResult(
        response=raw_output,
        path=path,
        query=query,
        records=len(my_df),
        columns=list(my_df.columns)
    )