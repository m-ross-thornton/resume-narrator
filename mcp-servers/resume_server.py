#!/usr/bin/env python3
"""Startup script for resume PDF server"""

import sys
import asyncio
import inspect
from resume_pdf_server import mcp

if __name__ == "__main__":
    try:
        # Check if mcp.run() is a coroutine function
        if inspect.iscoroutinefunction(mcp.run):
            asyncio.run(mcp.run())
        else:
            # If it's not async, call it directly
            result = mcp.run()
            # If it returns a coroutine, run it
            if inspect.iscoroutine(result):
                asyncio.run(result)
    except KeyboardInterrupt:
        print("\nResume server stopped")
        sys.exit(0)
    except Exception as e:
        print(f"Error in resume server: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
