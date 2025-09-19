# ui_client.py - Qwen3-8B: reasoning + tool streaming
import asyncio, json, os, hashlib
from typing import Any, Dict, AsyncGenerator
import streamlit as st
from agents.graph import graph

from agents.agent_state import AgentState
from langchain_core.messages import ToolMessage
from agents.tools import model_with_tools
from settings.loader import get

# ──────────────────────────────  Page Config  ──────────────────────────────
st.set_page_config(page_title="AI Assistant", page_icon="🤖", layout="centered")
st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.tool-output { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; }
.success-msg { color: #28a745; font-weight: 500; }
.wait-msg { color: #ff9900; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────── Session State ──────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "download_counter" not in st.session_state:
    st.session_state.download_counter = 0
if "last_tool_outputs" not in st.session_state:
    st.session_state.last_tool_outputs = {}

# ────────────────────────────── Helper Functions ──────────────────────────────
def generate_unique_key(filename: str) -> str:
    st.session_state.download_counter += 1
    hash_obj = hashlib.md5(f"{filename}_{st.session_state.download_counter}".encode())
    return f"download_{hash_obj.hexdigest()[:8]}"

def extract_file_path(output: Any) -> str:
    if isinstance(output, dict):
        if "path" in output and output["path"]:
            return output["path"]
        if "csv_file" in output and output["csv_file"]:
            return output["csv_file"]
    return ""

def display_tool_result(tool_name: str, output: Any):
    st.markdown(f'<div class="tool-output">', unsafe_allow_html=True)
    st.markdown(f"**🔧 {tool_name}**")
    if isinstance(output, dict):
        if "message" in output:
            st.markdown(f'<p class="success-msg">✅ {output["message"]}</p>', unsafe_allow_html=True)
        file_path = extract_file_path(output)
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            try:
                with open(file_path, "rb") as f:
                    mime_type = "text/csv" if filename.endswith(".csv") else "application/octet-stream"
                    st.download_button(
                        label=f"📥 Download {filename}",
                        data=f.read(),
                        file_name=filename,
                        mime=mime_type,
                        use_container_width=True,
                        key=generate_unique_key(file_path)
                    )
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

def should_filter_content(content: str) -> bool:
    if not content.strip(): return False
    filter_patterns = ["ScrapeResult", '"path":', '"message":', '"csv_file":']
    for pattern in filter_patterns:
        if pattern in content:
            return True
    try:
        parsed = json.loads(content.strip())
        if isinstance(parsed, dict) and any(k in parsed for k in ["path", "csv_file", "message"]):
            return True
    except: pass
    return False

# ────────────────────────────── Agent + Tools ──────────────────────────────
tools, model = model_with_tools()
tools_by_name = {t.name: t for t in tools}

async def stream_agent_with_tools_qwen(user_query: str, tool_container) -> AsyncGenerator[str, None]:
    """Stream reasoning first, then show tool wait message, then tool results."""
    inputs = {"messages": [("user", user_query)]}
    reasoning_done = False
    tool_wait_displayed = False
    final_tool_outputs = {}

    async for mode, chunk in graph.astream(inputs, stream_mode=["values", "messages"]):
        # Phase 1: Stream reasoning as soon as model emits content
        if mode == "messages":
            msg_chunk, _ = chunk
            if hasattr(msg_chunk, "content") and msg_chunk.content:
                content = msg_chunk.content
                if not should_filter_content(content):
                    yield content
                    reasoning_done = True

        # Phase 2: Detect tool calls & show wait immediately
        elif mode == "values":
            state = chunk
            if "tool_outputs" in state and state["tool_outputs"]:
                # If wait message not shown yet
                if not tool_wait_displayed:
                    tool_wait_displayed = True
                    with tool_container:
                        st.markdown('⏳ Collecting data, please wait...', unsafe_allow_html=True)

                # Display tool results once available
                current_tools = state["tool_outputs"]
                final_tool_outputs.update(current_tools)
                for tool_name, output in current_tools.items():
                    with tool_container:
                        display_tool_result(tool_name, output)

    # Save tool outputs to session state for persistence
    if final_tool_outputs:
        st.session_state.last_tool_outputs = final_tool_outputs

# ────────────────────────────── Display Message ──────────────────────────────
def display_message(msg: Dict[str, Any]):
    role = msg.get("role")
    content = msg.get("content")
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    elif role == "assistant":
        with st.chat_message("assistant"):
            st.markdown(content)
    elif role == "tool":
        with st.chat_message("assistant"):
            with st.expander("🔧 Tool Results", expanded=True):
                if isinstance(content, dict):
                    for tool_name, output in content.items():
                        display_tool_result(tool_name, output)

# ────────────────────────────── Main UI ──────────────────────────────
st.title("🤖 AI Assistant")
st.markdown("*Ask questions, get data, download results*")

# Display chat history
for message in st.session_state.messages:
    display_message(message)

# Chat input
if prompt := st.chat_input("What can I help you with?", disabled=st.session_state.is_processing):
    st.session_state.messages.append({"role": "user", "content": prompt})
    display_message(st.session_state.messages[-1])
    st.session_state.is_processing = True

    with st.status("🔄 Processing your request...", expanded=False) as status:
        try:
            tool_message = st.chat_message("assistant")
            tool_container = tool_message.container()
            assistant_message = st.chat_message("assistant")

            with assistant_message:
                final_response = st.write_stream(
                    stream_agent_with_tools_qwen(prompt, tool_container)
                )

            if final_response and final_response.strip():
                st.session_state.messages.append({"role": "assistant", "content": final_response})
            if st.session_state.last_tool_outputs:
                st.session_state.messages.append({"role": "tool", "content": st.session_state.last_tool_outputs})

            status.update(label="✅ Complete!", state="complete", expanded=False)

        except Exception as e:
            st.error(f"Error: {str(e)}")
            status.update(label="❌ Error", state="error")
        finally:
            st.session_state.is_processing = False

    st.rerun()

# Footer
st.markdown("---")
st.caption("Your Personal AI assistant")
