FROM python:3.11-slim

WORKDIR /app

COPY generator.py .

RUN pip install fastapi uvicorn

ENV PORT=3001

ENTRYPOINT ["sh", "-c", "uvicorn generator:app --host 0.0.0.0 --port $PORT"]
