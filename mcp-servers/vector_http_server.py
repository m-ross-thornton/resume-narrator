#!/usr/bin/env python3
"""
HTTP server wrapper for vector database MCP server
Launches uvicorn with FastMCP HTTP app
"""

import uvicorn
from vector_db_server import mcp

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        mcp.http_app,
        host="0.0.0.0",
        port=9002,
        log_level="info",
    )
