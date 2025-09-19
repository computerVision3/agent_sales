import asyncio
from agents.graph import graph


async def run_agent():
    print("Welcome to the agent!")
    while True:
        user_query = input("Enter your query: ").strip()
        if user_query.lower() in {"quit", "exit"}:
            break
        if not user_query:
            continue

        # Initialize input dynamically
        inputs = {"messages": [("user", user_query)]}

        # Async streaming loop from LangGraph
        async for state in graph.astream(inputs, stream_mode="values"):
            last_message = state.get("messages", [])[-1] if state.get("messages") else None
            if last_message:
                last_message.pretty_print()

            # Optional: print tool outputs if available
            tool_outputs = getattr(state, "tool_outputs", None)
            if tool_outputs:
                print("Tool outputs:", tool_outputs)


if __name__ == "__main__":
    asyncio.run(run_agent())
