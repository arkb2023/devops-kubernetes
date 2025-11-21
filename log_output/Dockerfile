FROM python:3.11-slim

WORKDIR /app

COPY log_output.py .

RUN pip install fastapi uvicorn

ENV PORT=3000

ENTRYPOINT ["sh", "-c", "uvicorn log_output:app --host 0.0.0.0 --port $PORT"]
