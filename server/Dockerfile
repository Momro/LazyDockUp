FROM python:3.11-slim
WORKDIR /app
# Wir kopieren alles aus dem server-Ordner
COPY . .
RUN pip install flask requests packaging
EXPOSE 5000
# WICHTIG: Kein Puffer, damit wir Logs sofort sehen
ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py"]
