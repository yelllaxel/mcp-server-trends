FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server code
COPY server.py .

# Cloud Run expects the container to listen on 8080
EXPOSE 8080

CMD ["python", "server.py"]