"""Run against a live local server: python tests/mcp_smoke.py URL."""

import asyncio
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    async with streamable_http_client(f"{base_url}/mcp") as (read, write, _), ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
        names = {tool.name for tool in tools.tools}
        expected = {
            "get_call_context",
            "record_call_started",
            "save_quote_progress",
            "save_negotiation_result",
            "mark_call_failure",
        }
        assert names == expected, (names, expected)
        print("mcp-smoke-ok", sorted(names))


if __name__ == "__main__":
    asyncio.run(main())
