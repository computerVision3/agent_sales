from agents.agent_state import AgentState
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableConfig
from agents.tools import model_with_tools 




tools, model = model_with_tools()
tools_by_name = {tool.name: tool for tool in tools}

# Define our tool node
async def call_tool(state: AgentState):
    outputs = []
    tool_outputs = {}
    # Iterate over the tool calls in the last message
    for tool_call in state["messages"][-1].tool_calls:      # type: ignore
        # Get the tool by name
        tool_result = await tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
        tool_outputs.update({tool_call["name"]: tool_result})
        outputs.append(
            ToolMessage(
                content=tool_result,
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
    return {"messages": outputs, "tool_outputs": tool_outputs}

async def call_model(
    state: AgentState,
    config: RunnableConfig,
):
    # Invoke the model with the system prompt and the messages
    response = await model.ainvoke(state["messages"], config)
    # We return a list, because this will get added to the existing messages state using the add_messages reducer
    return {"messages": [response]}


# Define the conditional edge that determines whether to continue or not
async def should_continue(state: AgentState):
    messages = state["messages"]
    # If the last message is not a tool call, then we finish
    if not messages[-1].tool_calls:     # type: ignore
        return "end"
    # default to continue
    return "continue"