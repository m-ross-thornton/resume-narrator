FROM python:3.11-slim

WORKDIR /auto-updater

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy webhook listener and update script
COPY webhook_listener.py .
COPY auto_update_resnar.sh .

# Make the update script executable
RUN chmod +x auto_update_resnar.sh

EXPOSE 8008

CMD ["python", "webhook_listener.py"]
