FROM python:3.11-alpine
# Installiere NUR die CLI und das Compose-Plugin (keinen Docker-Daemon!)
RUN apk add --no-cache docker-cli docker-cli-compose
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir flask docker
ENV PYTHONUNBUFFERED=1
EXPOSE 5001
CMD ["python", "agent.py"]

