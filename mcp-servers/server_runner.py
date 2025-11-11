#!/usr/bin/env python3
"""
Unified runner for all MCP HTTP servers
Launches each server in a separate subprocess
"""

import subprocess
import sys
import signal
import time
from pathlib import Path

# Map server names to their HTTP server modules
SERVERS = {
    "resume": ("resume_http_server", 9001),
    "vector": ("vector_http_server", 9002),
    "code": ("code_http_server", 9003),
}


def start_all_servers():
    """Start all MCP servers in parallel"""
    server_dir = Path(__file__).parent
    processes = {}

    print("Starting all MCP HTTP servers...\n")

    for name, (module, port) in SERVERS.items():
        print(f"  • Starting {name} server on port {port}...")
        proc = subprocess.Popen(
            [sys.executable, str(server_dir / f"{module}.py")],
            cwd=str(server_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        processes[name] = proc
        time.sleep(0.5)  # Stagger server starts

    print("\n✓ All servers started")
    print("\nServers available at:")
    for name, (module, port) in SERVERS.items():
        print(f"  • {name}: http://localhost:{port}")
    print("\nPress Ctrl+C to stop all servers.\n")

    def signal_handler(signum, frame):
        print("\n\nStopping all servers...")
        for name, proc in processes.items():
            try:
                proc.terminate()
                proc.wait(timeout=5)
                print(f"  ✓ {name} server stopped")
            except subprocess.TimeoutExpired:
                proc.kill()
                print(f"  ✓ {name} server killed")

        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Keep the processes running
    try:
        while True:
            time.sleep(1)
            # Check if any process has died
            for name, proc in list(processes.items()):
                if proc.poll() is not None:
                    print(f"\n⚠ {name} server exited unexpectedly")
                    # Restart it
                    print(f"  Restarting {name} server...")
                    module, port = SERVERS[name]
                    proc = subprocess.Popen(
                        [sys.executable, str(server_dir / f"{module}.py")],
                        cwd=str(server_dir),
                    )
                    processes[name] = proc
    except KeyboardInterrupt:
        signal_handler(None, None)


def start_single_server(server_name):
    """Start a single MCP server"""
    if server_name not in SERVERS:
        print(f"Unknown server: {server_name}")
        print(f"Available servers: {list(SERVERS.keys())}")
        sys.exit(1)

    module, port = SERVERS[server_name]
    server_dir = Path(__file__).parent

    print(f"Starting {server_name} server on port {port}...")
    subprocess.run(
        [sys.executable, str(server_dir / f"{module}.py")], cwd=str(server_dir)
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        if len(sys.argv) > 2:
            server_name = sys.argv[2]
            if server_name == "all":
                start_all_servers()
            else:
                start_single_server(server_name)
        else:
            print("Usage: python server_runner.py --server [resume|vector|code|all]")
            sys.exit(1)
    else:
        # Default: start all servers
        start_all_servers()
