from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from datetime import datetime
import uuid
import os
import logging
import httpx

# 1. CONFIGURE LOGGING FIRST
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger("log-output")
logger.setLevel(logging.DEBUG)  # DEBUG for testing

MESSAGE = os.getenv("MESSAGE", "hello world")
# GREETER_V1 = "http://greeter-svc-v1.exercises.svc.cluster.local:8000/greet"
# GREETER_V2 = "http://greeter-svc-v2.exercises.svc.cluster.local:8000/greet"
GREETER = "http://greeter-svc.exercises.svc.cluster.local:8000/greet"

async def lifespan(app: FastAPI):
    logger.debug("Lifespan startup: initializing resources")
    yield
    logger.debug("Lifespan shutdown: cleaning up resources")

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=PlainTextResponse)
async def root() -> PlainTextResponse:
    message = os.getenv("MESSAGE", "default message")
    logger.debug(f"Root endpoint environment: MESSAGE={message}")

    try:
        with open("/app/config/information.txt", "r") as file:
            file_content = file.read().strip()
    except Exception as e:
        logger.error(f"Error reading config file: {e}")
        file_content = "(error reading file)"

    pingpong_url = os.getenv("PINGPONG_APP_URL", "http://localhost:3000/pings")
    logger.debug(f"Root endpoint: fetching from {pingpong_url}")

    try:
        async with httpx.AsyncClient() as client:
            pong_response = await client.get(pingpong_url, timeout=5.0)
            pong_response.raise_for_status()
            pong_text = pong_response.text.strip()
            logger.debug(f"Root endpoint: received response with status {pong_response.status_code}")

    except httpx.RequestError as exc:
        logger.error(f"HTTP request error for {pingpong_url}: {exc}")
        pong_text = "(ping-pong service unreachable)"
    except httpx.HTTPStatusError as exc:
        logger.error(f"HTTP status error for {pingpong_url}: {exc}")
        pong_text = f"(ping-pong returned error {exc.response.status_code})"

    # Query greeter v1 + v2
    try:
        async with httpx.AsyncClient() as client:
            # v1_resp = await client.get(GREETER_V1, timeout=5.0)
            # v2_resp = await client.get(GREETER_V2, timeout=5.0)
            # greet_v1 = v1_resp.text.strip()
            # greet_v2 = v2_resp.text.strip()
            resp = await client.get(GREETER, timeout=5.0)
            greet = resp.text.strip()
    except:
        #greet_v1 = greet_v2 = "greeter unavailable"
        greet = "greeter unavailable"

    timestamp = datetime.utcnow().isoformat() + "Z"
    unique_id = str(uuid.uuid4())

    response_text = f"""
file_content: {file_content}
env variable: MESSAGE={message}
{timestamp}: {unique_id}.
{pong_text}
{greet}
"""
# Greeter v1: {greet_v1}
# Greeter v2: {greet_v2}
    return PlainTextResponse(response_text.strip())


@app.get("/healthz")
async def healthz():
    return {"status": "ready"}

# @app.get("/healthz")
# async def healthz():
#     try:
#         #pingpong_url = os.getenv("PINGPONG_APP_URL", "http://localhost:3000/pings")
#         #logger.debug(f"Root endpoint: fetching from {pingpong_url}")
#         #resp = await httpx.get(pingpong_url)
#         #resp.raise_for_status()
#         return {"status": "ready"}
#     except:
#         #logger.error(f"healthz: {pingpong_url} unresponsive")
#         raise HTTPException(503)
