FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir flask requests packaging apscheduler
EXPOSE 5000
ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py"]
