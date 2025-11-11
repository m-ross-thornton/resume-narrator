#!/usr/bin/env python3
"""
HTTP server wrapper for resume PDF MCP server
Launches uvicorn with FastMCP HTTP app
"""

import uvicorn
from resume_pdf_server import mcp

if __name__ == "__main__":
    # Run with uvicorn
    uvicorn.run(
        mcp.http_app,
        host="0.0.0.0",
        port=9001,
        log_level="info",
    )
