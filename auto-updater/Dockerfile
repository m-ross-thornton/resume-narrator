# Dockerfile (in the listener directory)
FROM python:3.11-slim
WORKDIR /auto-updater
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY webhook_listener.py .
EXPOSE 8008
CMD ["python", "webhook_listener.py"]
