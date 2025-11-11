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

            # Execute the deployment script asynchronously
            process = subprocess.Popen(
                ["bash", DEPLOY_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            logger.info(f"Deployment script initiated with PID: {process.pid}")

            return (
                jsonify(
                    {
                        "status": "deployment_initiated",
                        "message": "Deployment script has been started",
                        "pid": process.pid,
                        "script": DEPLOY_SCRIPT,
                    }
                ),
                200,
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


if __name__ == "__main__":
    logger.info("Starting GitHub Webhook Listener...")
    logger.info(f"Deployment script path: {DEPLOY_SCRIPT}")
    logger.info(f"Script exists: {os.path.exists(DEPLOY_SCRIPT)}")

    # Change host to '0.0.0.0' to make it accessible from outside the container/server
    app.run(host="0.0.0.0", port=8008, debug=False)
