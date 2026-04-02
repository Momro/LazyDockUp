FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://get.docker.com | sh
WORKDIR /app
COPY agent.py .
RUN pip install flask docker
ENV PYTHONUNBUFFERED=1
EXPOSE 5001
CMD ["python", "agent.py"]
