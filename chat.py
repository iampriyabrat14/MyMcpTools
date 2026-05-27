import asyncio
import json
import os
from openai import OpenAI
from fastmcp import Client
from dotenv import load_dotenv
from server import mcp

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"


def format_tool_result(result) -> str:
    if hasattr(result, "data"):
        data = result.data
    else:
        data = str(result)

    if isinstance(data, (dict, list)):
        return json.dumps(data, indent=2)
    return str(data)


async def run_chat():
    client = OpenAI(api_key=OPENAI_API_KEY)

    async with Client(mcp) as mcp_client:
        raw_tools = await mcp_client.list_tools()
        tools = [
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

        print("Gmail MCP Chat (OpenAI)")
        print("Type your message. Type 'exit' to quit.")
        print("-" * 40)

        messages = [
            {
                "role": "system",
                "content": "You are a Gmail assistant. Use the available tools to help the user read, send, search, and manage their emails. Always confirm before sending or deleting.",
            }
        ]

        while True:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Bye.")
                break

            messages.append({"role": "user", "content": user_input})

            while True:
                response = client.chat.completions.create(
                    model=MODEL,
                    tools=tools,
                    messages=messages,
                )

                message = response.choices[0].message
                messages.append(message)

                if response.choices[0].finish_reason == "stop":
                    print(f"\nAssistant: {message.content}")
                    break

                if response.choices[0].finish_reason == "tool_calls":
                    for tool_call in message.tool_calls:
                        print(f"\n[Calling tool: {tool_call.function.name} with {tool_call.function.arguments}]")
                        try:
                            args = json.loads(tool_call.function.arguments)
                            result = await mcp_client.call_tool(tool_call.function.name, args)
                            output = format_tool_result(result)
                        except Exception as e:
                            output = f"Tool error: {str(e)}"

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": output,
                        })


if __name__ == "__main__":
    asyncio.run(run_chat())
