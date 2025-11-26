from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from datetime import datetime
import uuid
import os
import logging
import httpx

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize resources on startup."""
    logger.debug(f"Lifespan startup: initializing resources")
    yield
    logger.debug(f"Lifespan shutdown: cleaning up resources")

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    async with httpx.AsyncClient() as client:
        # export PINGPONG_APP_URL=http://ping-pong-svc:3456/pings
        message = os.getenv("MESSAGE", "default message")
        logger.debug(f"Root endpoint environment: MESSAGE={message}")
        with open("/app/config/information.txt", "r") as file:
            file_content = file.read().strip()
        logger.debug(f"Root endpoint: MESSAGE={message}, file content={file_content}")
        pingpong_url = os.getenv("PINGPONG_APP_URL", "http://localhost:3000/pings")
        logger.debug(f"Root endpoint: fetching from {pingpong_url}")
        pong_response = await client.get(pingpong_url)
        logging.debug(f"Root endpoint: received response with status {pong_response.status_code}")
        pong_text = pong_response.text
        logger.debug(f"Root endpoint: response text {pong_text}")

    timestamp = datetime.utcnow().isoformat() + "Z"
    unique_id = str(uuid.uuid4())
    #return PlainTextResponse(f"{timestamp}: {unique_id}.\n{pong_text}")
    return PlainTextResponse(f"""
        file_content: {file_content}
        env variable: MESSAGE={message}
        {timestamp}: {unique_id}.
        {pong_text}
        """)
