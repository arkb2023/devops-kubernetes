# FROM python:3.11-slim

# WORKDIR /app

# COPY app/ ./app/

# RUN pip install fastapi uvicorn aiohttp pytest pytest-asyncio httpx jinja2 aiofiles
# ENV PORT=3000
# ENV CACHE_DIR=/usr/src/app/files/cache

# ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]

FROM python:3.12-slim

# Set work directory
WORKDIR /app

COPY app/ ./app/

RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source files
#COPY . .



#RUN chmod +x wait-for-it.sh
#ENV DB_HOST="localhost"
#ENV DB_PORT=5432
#ENV DB_NAME="tododb"
#ENV DB_USER="testdbuser"
#ENV DB_PASSWORD="testdbuserpassword"
ENV PORT=3000
# Expose port
#EXPOSE 8000

# Default startup command
#CMD ["./wait-for-it.sh", "db", "5432", "--", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
ENTRYPOINT ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port $PORT"]