#!/usr/bin/env python3
"""HTTP server for vector DB MCP server"""

import uvicorn
import sys
from vector_db_server import mcp

if __name__ == "__main__":
    # Get the ASGI app from FastMCP
    app = mcp.http_app()

    # Run with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9002, log_level="info")
