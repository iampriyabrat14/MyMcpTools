import asyncio
import json
import os
import threading
import streamlit as st
from openai import OpenAI
from fastmcp import Client
from dotenv import load_dotenv
from gmail.server import mcp
from gmail.summarizer import summarize_email_list, summarize_full_email
from gmail.digest import start_scheduler

load_dotenv()

MODEL = "gpt-4o"
SYSTEM_PROMPT = (
    "You are a Gmail assistant. Use the available tools to help the user "
    "read, send, search, reply to, and manage their emails. "
    "Always confirm before sending or deleting. "
    "When listing emails, present them clearly with subject, sender, and summary."
)


def format_tool_result(result) -> str:
    if hasattr(result, "data"):
        data = result.data
    else:
        data = str(result)
    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2)
    return str(data)


def get_mcp_tools():
    async def _fetch():
        async with Client(mcp) as mcp_client:
            raw_tools = await mcp_client.list_tools()
            return [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or "",
                        "parameters": t.inputSchema,
                    },
                }
                for t in raw_tools
            ]
    return asyncio.run(_fetch())


async def call_tool(tool_name: str, tool_args: dict) -> str:
    async with Client(mcp) as mcp_client:
        result = await mcp_client.call_tool(tool_name, tool_args)
        return format_tool_result(result)


def run_openai_turn(messages: list, tools: list) -> list:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    events = []

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            tools=tools,
            messages=messages,
        )

        message = response.choices[0].message
        messages.append(message)

        if response.choices[0].finish_reason == "stop":
            events.append({"type": "text", "content": message.content})
            break

        if response.choices[0].finish_reason == "tool_calls":
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                events.append({
                    "type": "tool_call",
                    "name": tool_name,
                    "args": tool_args,
                })

                try:
                    output = asyncio.run(call_tool(tool_name, tool_args))

                    parsed = json.loads(output) if output.startswith("[") or output.startswith("{") else output
                    if tool_name == "tool_list_emails" and isinstance(parsed, list):
                        parsed = summarize_email_list(parsed)
                        output = json.dumps(parsed, indent=2)

                except Exception as e:
                    output = f"Tool error: {str(e)}"

                events.append({
                    "type": "tool_result",
                    "name": tool_name,
                    "content": output,
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": output,
                })

    return events


def init_session():
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if "display" not in st.session_state:
        st.session_state.display = []
    if "tools" not in st.session_state:
        with st.spinner("Loading Gmail tools..."):
            st.session_state.tools = get_mcp_tools()
    if "scheduler_started" not in st.session_state:
        thread = threading.Thread(target=start_scheduler, daemon=True)
        thread.start()
        st.session_state.scheduler_started = True


def render_display():
    for item in st.session_state.display:
        if item["role"] == "user":
            with st.chat_message("user"):
                st.markdown(item["content"])

        elif item["role"] == "assistant":
            with st.chat_message("assistant"):
                st.markdown(item["content"])

        elif item["role"] == "tool_call":
            with st.expander(f"Tool called: {item['name']}", expanded=False):
                st.json(item["args"])

        elif item["role"] == "tool_result":
            with st.expander(f"Tool result: {item['name']}", expanded=False):
                try:
                    st.json(json.loads(item["content"]))
                except Exception:
                    st.text(item["content"])


def main():
    st.set_page_config(page_title="Gmail MCP Chat", page_icon="✉", layout="wide")
    st.title("Gmail MCP Chat")
    st.caption(f"Powered by OpenAI {MODEL} + FastMCP + Gmail API")

    init_session()

    with st.sidebar:
        st.header("Controls")
        if st.button("Clear Chat"):
            st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            st.session_state.display = []
            st.rerun()

        st.divider()
        st.subheader("Quick Actions")
        if st.button("Show Unread Emails"):
            st.session_state["prefill"] = "Show my unread emails with summaries"
        if st.button("Show Last 10 Emails"):
            st.session_state["prefill"] = "Show my last 10 emails"
        if st.button("Send Test Digest Now"):
            st.session_state["prefill"] = "Send me my daily email digest now"

        st.divider()
        st.subheader("Digest Schedule")
        digest_hour = os.getenv("DIGEST_HOUR", "8")
        digest_min = os.getenv("DIGEST_MINUTE", "0")
        st.info(f"Daily digest runs at {int(digest_hour):02d}:{int(digest_min):02d} every day")
        st.caption("Change DIGEST_HOUR and DIGEST_MINUTE in .env to reschedule")

    render_display()

    prefill = st.session_state.pop("prefill", "")
    user_input = st.chat_input("Ask about your emails...") or prefill

    if user_input:
        st.session_state.display.append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                events = run_openai_turn(
                    st.session_state.messages,
                    st.session_state.tools,
                )

            for event in events:
                if event["type"] == "tool_call":
                    st.session_state.display.append({
                        "role": "tool_call",
                        "name": event["name"],
                        "args": event["args"],
                    })
                    with st.expander(f"Tool called: {event['name']}", expanded=False):
                        st.json(event["args"])

                elif event["type"] == "tool_result":
                    st.session_state.display.append({
                        "role": "tool_result",
                        "name": event["name"],
                        "content": event["content"],
                    })
                    with st.expander(f"Tool result: {event['name']}", expanded=False):
                        try:
                            st.json(json.loads(event["content"]))
                        except Exception:
                            st.text(event["content"])

                elif event["type"] == "text":
                    st.session_state.display.append({
                        "role": "assistant",
                        "content": event["content"],
                    })
                    st.markdown(event["content"])


if __name__ == "__main__":
    main()
