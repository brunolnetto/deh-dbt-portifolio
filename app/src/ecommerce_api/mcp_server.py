"""Standalone MCP server entry point (stdio transport).

Usage:
    uv run python -m ecommerce_api.mcp_server
    # or from project root:
    python -m ecommerce_api.mcp_server

Claude Desktop config:
    {
      "mcpServers": {
        "ecommerce-analytics": {
          "command": "uv",
          "args": ["--directory", "/path/to/api", "run",
                   "python", "-m", "ecommerce_api.mcp_server"]
        }
      }
    }
"""

from .presentation.mcp.tools import mcp

if __name__ == "__main__":
    # MCPServer.run() manages its own event loop and calls the lifespan context
    mcp.run(transport="stdio")
