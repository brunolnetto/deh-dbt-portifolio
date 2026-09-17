"""Standalone MCP server entry point.

Run: python -m portfolio_api.mcp_server
This starts the MCP server over stdio (for Claude Desktop / MCP clients).
The HTTP transport is already available at POST /mcp when running the FastAPI app.
"""

import asyncio

from .presentation.mcp.tools import mcp


def main() -> None:
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
