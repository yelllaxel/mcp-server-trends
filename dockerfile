FROM python:3.12-slim

# Install MariaDB (MySQL-compatible) alongside Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    mariadb-server mariadb-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY mcp_serv/mcp_docker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp_serv/mcp_docker/server.py .
COPY mcp_serv/db_docker/01_trend_sample.sql /docker-entrypoint-initdb.d/01_trend_sample.sql
COPY mcp_serv/db_docker/02_create_user.sql /docker-entrypoint-initdb.d/02_create_user.sql

COPY start.sh .
RUN chmod +x start.sh

EXPOSE 8080
CMD ["./start.sh"]