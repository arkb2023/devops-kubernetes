FROM python:3.11-slim

WORKDIR /app

COPY pingpong.py .

RUN pip install fastapi uvicorn sqlalchemy asyncpg

ENV PORT=3000

ENTRYPOINT ["sh", "-c", "uvicorn pingpong:app --host 0.0.0.0 --port $PORT"]
