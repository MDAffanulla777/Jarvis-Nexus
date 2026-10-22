import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    url = "http://127.0.0.1:8001/mcp"

    print("Connecting to JARVIS Nexus MCP server...")

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:

            await session.initialize()
            print("MCP connection successful!")

            result = await session.list_tools()

            print("\nAvailable MCP tools:")

            for tool in result.tools:
                print(f"- {tool.name}: {tool.description}")

            print("\nTesting list_reminders...")

            result = await session.call_tool("list_reminders", {})

            for item in result.content:
                if hasattr(item, "text"):
                    print(item.text)


if __name__ == "__main__":
    asyncio.run(main())