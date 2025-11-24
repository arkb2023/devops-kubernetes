FROM python:3.11-slim

WORKDIR /app

COPY main.py .

RUN pip install fastapi uvicorn aiohttp pytest pytest-asyncio httpx
ENV PORT=3000
ENV CACHE_DIR=/usr/src/app/files/cache

ENTRYPOINT ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
