from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from datetime import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Counter:
    def __init__(self):
        self.counter = 0

    def incr(self):
        self.counter += 1
        return self.counter

    def set(self, value):
        self.counter = value

    def get(self):
        return self.counter

async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize resources on startup."""
    global counter
    logger.debug(f"Lifespan startup: initializing Counter")
    counter = Counter()
    yield
    logger.debug(f"Lifespan shutdown: cleaning up resources")

    
# Counter global
counter: Counter | None = None  # type hint for clarity
app = FastAPI(lifespan=lifespan)

@app.get("/pings")
async def get_pong_count():
    pong_count = counter.get()
    return PlainTextResponse(f"Ping / Pongs: {pong_count}")

@app.get("/pingpong", response_class=PlainTextResponse)
async def pingpong():
    # Increment and write the pingpong request count
    request_count = counter.incr()
    return f"pong: {request_count}\n"

@app.on_event("startup")
async def startup_event():
    logger.debug(f"Startup event: processing started.")
