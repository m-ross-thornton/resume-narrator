from flask import Flask, request, abort
import subprocess
import os

app = Flask(__name__)
# Replace with the actual path to your deployment script
DEPLOY_SCRIPT = "/app/auto_update_resnar.sh"

# You should secure this endpoint in a real-world scenario (e.g., using GitHub secrets)
@app.route('/github_listener', methods=['POST'])
def webhook():
    if request.method == 'POST':
        # Execute the deployment script
        subprocess.Popen(['bash', DEPLOY_SCRIPT])
        print("Deployment script initiated...")
        return 'Deployment initiated', 200
    else:
        abort(400)

if __name__ == '__main__':
    # Change host to '0.0.0.0' to make it accessible from outside the container/server
    app.run(host='0.0.0.0', port=8008)
