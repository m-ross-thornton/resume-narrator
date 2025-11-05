# mcp_servers/server_runner.py
"""
Unified runner for all MCP servers
Can run individual servers or all servers together
"""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List
import signal
import os


class MCPServerManager:
    """Manage multiple MCP servers via subprocess"""

    # Map of server names to their startup scripts
    SERVERS = {
        "resume": "resume_server.py",
        "vector": "vector_server.py",
        "code": "code_server.py",
    }

    def __init__(self):
        self.server_dir = Path(__file__).parent
        self.processes = {}

    def run_server(self, server_name: str):
        """Run a single MCP server"""
        if server_name not in self.SERVERS:
            print(f"Unknown server: {server_name}")
            print(f"Available servers: {list(self.SERVERS.keys())}")
            sys.exit(1)

        script = self.SERVERS[server_name]
        script_path = self.server_dir / script

        print(f"Starting {server_name} MCP server...")

        try:
            # Run the server script
            subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.server_dir),
            )
        except KeyboardInterrupt:
            print(f"\n{server_name} server stopped")
        except Exception as e:
            print(f"Error running {server_name} server: {e}")
            sys.exit(1)

    def run_all_servers(self):
        """Run all MCP servers concurrently as subprocesses"""
        print("Starting all MCP servers...")

        processes = {}
        for name, script in self.SERVERS.items():
            script_path = self.server_dir / script
            print(f"  - Starting {name} server...")

            try:
                # Run server subprocess with inherited stdio
                # FastMCP servers communicate via stdio
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=str(self.server_dir),
                    stdin=subprocess.DEVNULL,  # Not accepting interactive input in Docker
                    # Keep stdout/stderr connected to parent (Docker container output)
                )
                processes[name] = process
            except Exception as e:
                print(f"Error starting {name} server: {e}")

        print(f"All {len(processes)} servers are running. Press Ctrl+C to stop.")

        def signal_handler(signum, frame):
            print("\nStopping all servers...")
            for name, process in processes.items():
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception as e:
                    print(f"Error stopping {name} server: {e}")
                    process.kill()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Keep the process alive and monitor servers
            # Even if all subprocesses exit, keep the main process running
            # (in case MCP clients reconnect later)
            while True:
                # Check if any process has exited
                remaining = {}
                for name, process in processes.items():
                    if process.poll() is None:
                        remaining[name] = process
                    else:
                        print(f"Server {name} exited with code {process.returncode}")
                        # Optionally: restart the server
                        # For now, just leave it down
                processes = remaining

                # Sleep briefly to avoid busy-waiting
                import time

                time.sleep(5)

        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)


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

    try:
        manager = MCPServerManager()

        if args.server == "all":
            manager.run_all_servers()
        else:
            manager.run_server(args.server)

    except KeyboardInterrupt:
        print("\nServer stopped")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
