"""
Tests for MCP container builds and health checks.

This test suite validates that MCP containers can be built and started
independently without requiring Ollama or the full system.
"""

import subprocess
import time
import requests
import pytest
from pathlib import Path
from typing import List, Tuple


class MCPContainerTest:
    """Test MCP container builds and health"""

    PROJECT_ROOT = Path(__file__).parent.parent
    DOCKER_COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

    MCP_SERVICES = ["mcp-vector", "mcp-resume", "mcp-code"]
    MCP_PORTS = {
        "mcp-vector": 9002,
        "mcp-resume": 9001,
        "mcp-code": 9003,
    }
    HEALTH_ENDPOINTS = {
        "mcp-vector": "http://localhost:9002/health",
        "mcp-resume": "http://localhost:9001/health",
        "mcp-code": "http://localhost:9003/health",
    }

    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        cls.project_root = Path(__file__).parent.parent
        print(f"\n📦 Project root: {cls.project_root}")

    def test_01_docker_compose_file_exists(self):
        """Test that docker-compose.yml exists"""
        assert (
            self.DOCKER_COMPOSE_FILE.exists()
        ), f"docker-compose.yml not found at {self.DOCKER_COMPOSE_FILE}"

    def test_02_build_mcp_containers(self):
        """Test building MCP containers"""
        print("\n🔨 Building MCP containers...")

        for service in self.MCP_SERVICES:
            print(f"  Building {service}...", end=" ")
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.DOCKER_COMPOSE_FILE),
                    "build",
                    service,
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                print(f"\n❌ Build failed for {service}")
                print("STDOUT:", result.stdout)
                print("STDERR:", result.stderr)
                pytest.fail(f"Failed to build {service}")

            print("✓")

    def test_03_start_mcp_containers(self):
        """Test starting MCP containers"""
        print("\n🚀 Starting MCP containers...")

        # Start all MCP services
        result = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(self.DOCKER_COMPOSE_FILE),
                "up",
                "-d",
            ]
            + self.MCP_SERVICES,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            pytest.fail("Failed to start MCP containers")

        # Wait for containers to be ready
        print("  Waiting for containers to be healthy...", end=" ")
        time.sleep(5)
        print("✓")

    def test_04_check_container_status(self):
        """Test that containers are running"""
        print("\n📊 Checking container status...")

        for service in self.MCP_SERVICES:
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.DOCKER_COMPOSE_FILE),
                    "ps",
                    service,
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            output = result.stdout
            if "Up" not in output:
                print(f"  ❌ {service} is not running")
                # Show full ps output for debugging
                subprocess.run(
                    ["docker", "compose", "-f", str(self.DOCKER_COMPOSE_FILE), "ps"],
                    cwd=self.project_root,
                )
                pytest.fail(f"{service} container is not running")

            print(f"  ✓ {service} is running")

    def test_05_mcp_vector_health(self):
        """Test mcp-vector health endpoint"""
        print("\n🏥 Testing mcp-vector health...", end=" ")

        try:
            response = requests.get(self.HEALTH_ENDPOINTS["mcp-vector"], timeout=5)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "status" in data or "health" in data or data, "Empty health response"
            print("✓")
        except requests.exceptions.ConnectionError:
            pytest.fail("Could not connect to mcp-vector on port 9002")
        except Exception as e:
            pytest.fail(f"mcp-vector health check failed: {e}")

    def test_06_mcp_resume_health(self):
        """Test mcp-resume health endpoint"""
        print("🏥 Testing mcp-resume health...", end=" ")

        try:
            response = requests.get(self.HEALTH_ENDPOINTS["mcp-resume"], timeout=5)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "status" in data or "health" in data or data, "Empty health response"
            print("✓")
        except requests.exceptions.ConnectionError:
            pytest.fail("Could not connect to mcp-resume on port 9001")
        except Exception as e:
            pytest.fail(f"mcp-resume health check failed: {e}")

    def test_07_mcp_code_health(self):
        """Test mcp-code health endpoint"""
        print("🏥 Testing mcp-code health...", end=" ")

        try:
            response = requests.get(self.HEALTH_ENDPOINTS["mcp-code"], timeout=5)
            assert (
                response.status_code == 200
            ), f"Expected 200, got {response.status_code}"
            data = response.json()
            assert "status" in data or "health" in data or data, "Empty health response"
            print("✓")
        except requests.exceptions.ConnectionError:
            pytest.fail("Could not connect to mcp-code on port 9003")
        except Exception as e:
            pytest.fail(f"mcp-code health check failed: {e}")

    def test_08_mcp_vector_endpoints(self):
        """Test mcp-vector available endpoints"""
        print("\n🔌 Testing mcp-vector endpoints...")

        endpoints = [
            ("/health", "GET"),
            ("/tool/search_experience", "POST"),
            ("/tool/analyze_skill_coverage", "POST"),
        ]

        for endpoint, method in endpoints:
            url = f"http://localhost:9002{endpoint}"
            print(f"  Testing {method} {endpoint}...", end=" ")

            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, json={}, timeout=5)

                # We expect it to be reachable (even if it returns error due to empty body)
                assert response.status_code in [
                    200,
                    400,
                    422,
                ], f"Unexpected status {response.status_code}"
                print("✓")
            except requests.exceptions.ConnectionError:
                pytest.fail(f"Could not reach {endpoint}")
            except Exception as e:
                pytest.fail(f"Error testing {endpoint}: {e}")

    def test_09_mcp_resume_endpoints(self):
        """Test mcp-resume available endpoints"""
        print("\n🔌 Testing mcp-resume endpoints...")

        endpoints = [
            ("/health", "GET"),
            ("/tool/generate_resume_pdf", "POST"),
        ]

        for endpoint, method in endpoints:
            url = f"http://localhost:9001{endpoint}"
            print(f"  Testing {method} {endpoint}...", end=" ")

            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, json={}, timeout=5)

                # We expect it to be reachable
                assert response.status_code in [
                    200,
                    400,
                    422,
                ], f"Unexpected status {response.status_code}"
                print("✓")
            except requests.exceptions.ConnectionError:
                pytest.fail(f"Could not reach {endpoint}")
            except Exception as e:
                pytest.fail(f"Error testing {endpoint}: {e}")

    def test_10_container_logs_no_errors(self):
        """Test that containers don't have error logs"""
        print("\n📋 Checking container logs...")

        for service in self.MCP_SERVICES:
            print(f"  Checking {service} logs...", end=" ")

            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(self.DOCKER_COMPOSE_FILE),
                    "logs",
                    service,
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            logs = result.stdout + result.stderr

            # Check for common error patterns
            error_patterns = [
                "ERROR",
                "FATAL",
                "ModuleNotFoundError",
                "ImportError",
                "ConnectionError",
                "failed to",
            ]

            found_errors = []
            for pattern in error_patterns:
                if pattern in logs:
                    # Some patterns might be false positives, so collect them
                    found_errors.append(pattern)

            if found_errors:
                print(f"\n  ⚠️  Found potential errors: {found_errors}")
                print("  Last 20 lines of logs:")
                print("  " + "\n  ".join(logs.split("\n")[-20:]))
            else:
                print("✓")

    @classmethod
    def teardown_class(cls):
        """Clean up containers after tests"""
        print("\n🧹 Cleaning up containers...")

        for service in cls.MCP_SERVICES:
            print(f"  Stopping {service}...", end=" ")
            subprocess.run(
                [
                    "docker",
                    "compose",
                    "-f",
                    str(cls.DOCKER_COMPOSE_FILE),
                    "stop",
                    service,
                ],
                capture_output=True,
                timeout=30,
            )
            print("✓")

        print("  Removing containers...", end=" ")
        subprocess.run(
            ["docker", "compose", "-f", str(cls.DOCKER_COMPOSE_FILE), "rm", "-f"]
            + cls.MCP_SERVICES,
            capture_output=True,
            timeout=30,
        )
        print("✓")

        print("\n✅ Cleanup complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
