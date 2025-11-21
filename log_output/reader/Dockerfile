FROM python:3.11-slim

WORKDIR /app

COPY reader.py .

RUN pip install fastapi uvicorn

ENV PORT=3000

ENTRYPOINT ["sh", "-c", "uvicorn reader:app --host 0.0.0.0 --port $PORT"]
