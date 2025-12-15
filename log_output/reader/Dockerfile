FROM python:3.11-slim

WORKDIR /app

# System packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY reader.py .

ENV PINGPONG_APP_URL=http://ping-pong-svc:3456/pings
ENV PORT=3000

ENTRYPOINT ["sh", "-c", "uvicorn reader:app --host 0.0.0.0 --port $PORT"]
