FROM python:3.11-slim

WORKDIR /app

COPY app/ ./app/

RUN pip install fastapi uvicorn aiohttp pytest pytest-asyncio httpx jinja2 aiofiles
ENV PORT=3000
ENV CACHE_DIR=/usr/src/app/files/cache

ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]
