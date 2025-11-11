#!/usr/bin/env python3
"""
Test MCP server connectivity
Starts all servers and verifies they respond to health checks
"""

import subprocess
import sys
import time
import httpx
from pathlib import Path


def test_health_check(name: str, port: int, max_retries: int = 30) -> bool:
    """Test if a server is running and responding to health checks"""
    url = f"http://localhost:{port}/health"

    for attempt in range(max_retries):
        try:
            response = httpx.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                print(f"✓ {name} server (port {port}) is healthy")
                print(f"  Response: {data}")
                return True
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.PoolTimeout):
            if attempt < max_retries - 1:
                print(f"  {name}: waiting... ({attempt + 1}/{max_retries})", end="\r")
                time.sleep(1)
        except Exception as e:
            print(f"✗ {name} error: {e}")
            return False

    print(f"✗ {name} server did not respond within {max_retries}s")
    return False


def main():
    """Start servers and run health checks"""
    project_root = Path(__file__).parent
    mcp_dir = project_root / "mcp-servers"

    print("=" * 60)
    print("MCP Server Connectivity Test")
    print("=" * 60)
    print()

    # Start all servers
    print("Starting MCP servers...")
    proc = subprocess.Popen(
        [sys.executable, str(mcp_dir / "server_runner.py"), "--server", "all"],
        cwd=str(mcp_dir),
    )

    # Wait for servers to start
    time.sleep(5)

    # Test connectivity
    print("\nTesting server health checks:\n")
    results = {
        "resume": test_health_check("resume", 9001),
        "vector": test_health_check("vector", 9002),
        "code": test_health_check("code", 9003),
    }

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name} server")

    # Cleanup
    print("\nShutting down servers...")
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

    # Return exit code based on results
    all_passed = all(results.values())
    print(f"\n{'✓ All tests passed!' if all_passed else '✗ Some tests failed'}")
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
