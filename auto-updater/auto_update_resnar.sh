#!/bin/bash

# Navigate to the root directory of your project
cd /host/project

echo "Starting git pull..."
# Pull the latest changes from the GitHub repository
git pull origin main || { echo "Git pull failed!"; exit 1; }

echo "Starting docker build and deployment..."
# Build the images and start the containers in detached mode
# The --build flag forces a rebuild of the images, which is usually necessary after a code change.
docker compose up -d --build || { echo "Docker compose failed!"; exit 1; }

echo "Deployment complete."
