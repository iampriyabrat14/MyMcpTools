from fastmcp import FastMCP, Client
import asyncio

mcp = FastMCP("MyServer")

@mcp.tool()
def greet(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"

async def main():
    async with Client(mcp) as client:
        result = await client.call_tool("greet", {"name": "Priyabrat"})
        print(result.data)   # Hello, Priyabrat!

asyncio.run(main())
