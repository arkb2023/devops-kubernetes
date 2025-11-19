FROM python:3.11-slim

WORKDIR /app

COPY main.py .

RUN pip install fastapi uvicorn

ENV PORT=8000

ENTRYPOINT ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
