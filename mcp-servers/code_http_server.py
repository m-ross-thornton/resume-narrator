#!/usr/bin/env python3
"""
HTTP server wrapper for code explorer MCP server
Launches uvicorn with FastMCP HTTP app
"""

import uvicorn
from code_explorer_server import mcp

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        mcp.http_app,
        host="0.0.0.0",
        port=9003,
        log_level="info",
    )
