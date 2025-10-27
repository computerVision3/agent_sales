# from agents.agent_state import AgentState
# from langchain_core.messages import ToolMessage, HumanMessage, AIMessage
# from langchain_core.runnables import RunnableConfig
# from agents.tools import model_with_tools 
# from langchain_postgres import PostgresChatMessageHistory

# from dotenv import load_dotenv, find_dotenv

# from settings.db import init_db

# load_dotenv(find_dotenv())

# # ----------------- Setup tools/model -----------------
# tools, model = model_with_tools()
# tools_by_name = {tool.name: tool for tool in tools}

# # ----------------- Create chat session -----------------
# async def chat_session(session_id: str):
#     conn = await init_db()
#     chat_history = PostgresChatMessageHistory("chat_history", session_id, async_connection=conn)
#     return chat_history

# # ----------------- Helper to add user message -----------------
# async def add_user_message(content: str, state: AgentState, chat_history: PostgresChatMessageHistory):
#     msg = HumanMessage(content=content)
#     await chat_history.aadd_messages([msg])
#     state["messages"].append(msg)

# # ----------------- Define tool node -----------------
# async def call_tool(state: AgentState):
#     chat_history = state.get("chat_history")
#     outputs = []
#     tool_outputs = {}
#     last_msg = state["messages"][-1]

#     if getattr(last_msg, "tool_calls", None):
#         for tool_call in last_msg.tool_calls:
#             tool_result = await tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
#             tool_outputs[tool_call["name"]] = tool_result

#             tool_msg = ToolMessage(
#                 content=tool_result,
#                 name=tool_call["name"],
#                 tool_call_id=tool_call["id"]
#             )
#             if chat_history:
#                 await chat_history.aadd_messages([tool_msg])
#             outputs.append(tool_msg)

#     state["tool_outputs"] = tool_outputs
#     return {"messages": outputs, "tool_outputs": tool_outputs}


# # ----------------- Define model node -----------------
# async def call_model(state: AgentState, config: RunnableConfig):
#     chat_history = state.get("chat_history")
#     if chat_history is not None:
#         response = await model.ainvoke(state["messages"], config)
#         await chat_history.aadd_messages([response])
#         state["messages"].append(response)
#         return {"messages": [response]}
#     else:
#         # fallback if somehow chat_history is missing
#         response = await model.ainvoke(state["messages"], config)
#         state["messages"].append(response)
#         return {"messages": [response]}

# # ----------------- Conditional edge -----------------
# # async def should_continue(state: AgentState):
# #     last_msg = state["messages"][-1]
# #     if not getattr(last_msg, "tool_calls", None):
# #         return "end"
# #     return "continue"

# async def should_continue(state: AgentState):
#     """
#     Decide whether to continue calling tools or stop the graph.
#     We check the LAST AIMessage (not the very last message, which could be a ToolMessage).
#     """
#     ai_msgs = [m for m in state["messages"] if isinstance(m, AIMessage)]
#     if ai_msgs and getattr(ai_msgs[-1], "tool_calls", None):
#         return "continue"
#     return "end"




from agents.agent_state import AgentState
from langchain_core.messages import ToolMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from agents.tools import model_with_tools
from langchain_postgres import PostgresChatMessageHistory

from dotenv import load_dotenv, find_dotenv
from settings.db import init_db

load_dotenv(find_dotenv())

# ----------------- Setup tools/model -----------------
tools, model = model_with_tools()
tools_by_name = {tool.name: tool for tool in tools}

# ----------------- System prompt -----------------
SYSTEM_PROMPT = """
You are LeadForge AI, an AI assistant exclusively for retrieving verified company details — specifically business phone numbers, email, addresses, and director/executive names.
Rules:
1. ONLY respond to queries within the above domains.
2. For ANY query outside these areas, reply EXACTLY:  
   "Hi, I’m LeadForge AI, your AI assistant for lead generation and business growth."
3. NEVER answer from internal knowledge. ALWAYS use tools (search, enrichment, template generation, etc.) to fulfill valid requests.
4. Before showing results, briefly state which tool you used.
5. Keep responses concise, structured, and actionable.
6. If a request can’t be fulfilled with available tools, say so and suggest an alternative.
"""

# ----------------- Create chat session -----------------
async def chat_session(session_id: str):
    """
    Initialize chat session.
    Returns:
        chat_history: PostgresChatMessageHistory object (DB)
        state_messages: list of messages (in-memory, includes system message)
    """
    conn = await init_db()
    chat_history = PostgresChatMessageHistory(
        "chat_history", session_id, async_connection=conn
    )
    
    # Load existing messages from DB
    db_messages = await chat_history.aget_messages()
    
    # In-memory messages with system prompt included (not stored in DB)
    state_messages = [SystemMessage(content=SYSTEM_PROMPT)] + db_messages
    
    return chat_history, state_messages

# ----------------- Helper to add user message -----------------
async def add_user_message(content: str, state: AgentState, chat_history: PostgresChatMessageHistory):
    """
    Add a user message to DB and in-memory state.
    """
    msg = HumanMessage(content=content)
    await chat_history.aadd_messages([msg])  # store user message in DB
    state["messages"].append(msg)            # store in in-memory state

# ----------------- Define tool node -----------------
async def call_tool(state: AgentState):
    """
    Execute any tool calls present in the last AI message.
    """
    chat_history = state.get("chat_history")
    outputs = []
    tool_outputs = {}

    last_msg = state["messages"][-1]

    if getattr(last_msg, "tool_calls", None):
        for tool_call in last_msg.tool_calls:
            tool_result = await tools_by_name[tool_call["name"]].ainvoke(tool_call["args"])
            tool_outputs[tool_call["name"]] = tool_result

            tool_msg = ToolMessage(
                content=tool_result,
                name=tool_call["name"],
                tool_call_id=tool_call["id"]
            )
            if chat_history:
                await chat_history.aadd_messages([tool_msg])  # store tool output in DB
            outputs.append(tool_msg)

    state["tool_outputs"] = tool_outputs
    return {"messages": outputs, "tool_outputs": tool_outputs}

# ----------------- Define model node -----------------
async def call_model(state: AgentState, config: RunnableConfig):
    """
    Call the model using in-memory messages (system message included).
    Only AI responses are stored in the DB.
    """
    chat_history = state.get("chat_history")
    
    # Model sees in-memory messages including system prompt
    response = await model.ainvoke(state["messages"], config)
    
    # Store AI response in DB only
    if chat_history:
        await chat_history.aadd_messages([response])
    
    state["messages"].append(response)
    return {"messages": [response]}

# ----------------- Conditional edge -----------------
async def should_continue(state: AgentState):
    """
    Decide whether to continue calling tools or stop the graph.
    Only checks the last AIMessage for tool calls.
    """
    ai_msgs = [m for m in state["messages"] if isinstance(m, AIMessage)]
    if ai_msgs and getattr(ai_msgs[-1], "tool_calls", None):
        return "continue"
    return "end"

# ----------------- Example usage -----------------
# Example:
# chat_history, state_messages = await chat_session("session_123")
# state = {"messages": state_messages, "chat_history": chat_history}
# await add_user_message("Find SaaS leads", state, chat_history)
# await call_model(state, config)
# await call_tool(state)
