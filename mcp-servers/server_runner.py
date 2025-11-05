# mcp_servers/server_runner.py
"""
Unified runner for all MCP servers
Can run individual servers or all servers together
"""

import asyncio
import sys
from pathlib import Path
import argparse
from typing import List, Optional

# Import all MCP servers
from resume_pdf_server import mcp as resume_mcp
from vector_db_server import mcp as vector_mcp
from code_explorer_server import mcp as code_mcp


class MCPServerManager:
    """Manage multiple MCP servers"""

    def __init__(self):
        self.servers = {"resume": resume_mcp, "vector": vector_mcp, "code": code_mcp}

    async def run_server(self, server_name: str):
        """Run a single MCP server"""
        if server_name not in self.servers:
            print(f"Unknown server: {server_name}")
            print(f"Available servers: {list(self.servers.keys())}")
            sys.exit(1)

        server = self.servers[server_name]
        print(f"Starting {server_name} MCP server...")

        try:
            await server.run()
        except KeyboardInterrupt:
            print(f"\n{server_name} server stopped")
        except Exception as e:
            print(f"Error running {server_name} server: {e}")
            sys.exit(1)

    async def run_all_servers(self):
        """Run all MCP servers concurrently"""
        print("Starting all MCP servers...")

        tasks = []
        for name, server in self.servers.items():
            print(f"  - Starting {name} server...")
            task = asyncio.create_task(server.run())
            tasks.append(task)

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nStopping all servers...")
            for task in tasks:
                task.cancel()
        except Exception as e:
            print(f"Error running servers: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run MCP servers")
    parser.add_argument(
        "--server",
        choices=["resume", "vector", "code", "all"],
        default="all",
        help="Which server to run (default: all)",
    )
    parser.add_argument(
        "--port", type=int, default=None, help="Port to run the server on"
    )

    args = parser.parse_args()

    manager = MCPServerManager()

    try:
        if args.server == "all":
            asyncio.run(manager.run_all_servers())
        else:
            asyncio.run(manager.run_server(args.server))
    except KeyboardInterrupt:
        print("\nServer stopped")
        sys.exit(0)
    except RuntimeError as e:
        error_msg = str(e).lower()
        if (
            "already running asyncio" in error_msg
            or "event loop is running" in error_msg
        ):
            print(f"Fatal error: {e}", file=sys.stderr)
            print(
                "The event loop is already running. This might be due to the FastMCP server initialization.",
                file=sys.stderr,
            )
            sys.exit(1)
        raise
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
