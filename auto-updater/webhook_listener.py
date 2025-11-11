from flask import Flask, request, abort, jsonify
import subprocess
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Path to deployment script - located in same directory
DEPLOY_SCRIPT = os.path.join(os.path.dirname(__file__), "auto_update_resnar.sh")


# You should secure this endpoint in a real-world scenario (e.g., using GitHub secrets)
@app.route("/github_listener", methods=["POST", "GET"])
def webhook():
    """Handle GitHub webhook for auto-deployment"""

    # Health check endpoint
    if request.method == "GET":
        return (
            jsonify(
                {
                    "status": "ok",
                    "service": "github-webhook-listener",
                    "timestamp": datetime.now().isoformat(),
                    "deploy_script": DEPLOY_SCRIPT,
                    "script_exists": os.path.exists(DEPLOY_SCRIPT),
                }
            ),
            200,
        )

    # Webhook handler
    if request.method == "POST":
        try:
            logger.info("GitHub webhook received")
            logger.info(f"Webhook payload: {request.json}")

            # Check if deployment script exists
            if not os.path.exists(DEPLOY_SCRIPT):
                logger.error(f"Deployment script not found at: {DEPLOY_SCRIPT}")
                return (
                    jsonify(
                        {"error": "Deployment script not found", "path": DEPLOY_SCRIPT}
                    ),
                    500,
                )

            logger.info(f"Executing deployment script: {DEPLOY_SCRIPT}")

            # Execute the deployment script and WAIT for it to complete
            # This allows us to capture output and see errors
            process = subprocess.Popen(
                ["bash", DEPLOY_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for process to complete and capture output
            stdout, stderr = process.communicate()
            return_code = process.returncode

            # Log all output
            if stdout:
                logger.info(f"Script output:\n{stdout}")
            if stderr:
                logger.error(f"Script error output:\n{stderr}")

            logger.info(f"Deployment script completed with return code: {return_code}")

            if return_code == 0:
                return (
                    jsonify(
                        {
                            "status": "deployment_success",
                            "message": "Deployment completed successfully",
                            "script": DEPLOY_SCRIPT,
                            "output": stdout,
                        }
                    ),
                    200,
                )
            else:
                return (
                    jsonify(
                        {
                            "status": "deployment_failed",
                            "message": f"Deployment script exited with code {return_code}",
                            "script": DEPLOY_SCRIPT,
                            "error": stderr,
                            "output": stdout,
                        }
                    ),
                    500,
                )

        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            return jsonify({"error": str(e), "status": "failed"}), 500

    abort(400)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return (
        jsonify(
            {
                "status": "ok",
                "service": "github-webhook-listener",
                "timestamp": datetime.now().isoformat(),
            }
        ),
        200,
    )


@app.route("/diagnose", methods=["GET"])
def diagnose():
    """Diagnostic endpoint to check deployment environment"""
    import subprocess

    diagnostics = {
        "timestamp": datetime.now().isoformat(),
        "docker_socket_exists": os.path.exists("/var/run/docker.sock"),
        "deploy_script_exists": os.path.exists(DEPLOY_SCRIPT),
        "deploy_script_path": DEPLOY_SCRIPT,
        "host_mount_exists": os.path.exists("/host/project"),
    }

    # Try to check available mount points
    try:
        mount_output = subprocess.check_output(["mount"], text=True)
        host_mounts = [line for line in mount_output.split("\n") if "/host" in line]
        diagnostics["host_mounts"] = (
            host_mounts if host_mounts else ["No /host mounts found"]
        )
    except:
        diagnostics["host_mounts"] = ["Failed to check mounts"]

    # Check if docker is accessible
    try:
        subprocess.run(["docker", "ps"], capture_output=True, timeout=5)
        diagnostics["docker_accessible"] = True
    except:
        diagnostics["docker_accessible"] = False

    # Check git config
    try:
        git_user = subprocess.check_output(
            ["git", "config", "user.name"], text=True, cwd="/host/project"
        ).strip()
        diagnostics["git_config_ok"] = True
        diagnostics["git_user"] = git_user
    except:
        diagnostics["git_config_ok"] = False
        diagnostics["git_user"] = "Not configured or /host/project not found"

    return jsonify(diagnostics), 200


if __name__ == "__main__":
    logger.info("Starting GitHub Webhook Listener...")
    logger.info(f"Deployment script path: {DEPLOY_SCRIPT}")
    logger.info(f"Script exists: {os.path.exists(DEPLOY_SCRIPT)}")

    # Change host to '0.0.0.0' to make it accessible from outside the container/server
    app.run(host="0.0.0.0", port=8008, debug=False)
