from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from datetime import datetime
import uuid
import os
import logging

app = FastAPI()

# Configure logger once at module level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get log directory from environment variable, default to "/usr/src/app/files"
# Shared volume mount path where Ping-pong app writes request count
shared_dir = os.getenv("LOG_DIR", "/usr/src/app/files")
request_count_file = os.path.join(shared_dir, "pingpong-requests.txt")

def read_request_count():
    try:
        with open(request_count_file, "r") as f:
            count = f.read().strip()
            logger.debug(f"DEBUG: {count} ping-pong requests read from {request_count_file}")
            return count
    except FileNotFoundError:
        logger.error(f"ERROR: {request_count_file} does not exist.")
        return "0"  # Return zero if file is missing initially

@app.get("/", response_class=PlainTextResponse)
def read_logs():
    # Generate current timestamp and random string (UUID)
    timestamp = datetime.utcnow().isoformat() + "Z"
    random_id = str(uuid.uuid4())
    logger.debug(f"DEBUG: Request received at {timestamp}: {random_id}")

    # Read persisted ping-pong request count
    request_count = read_request_count()

    logger.debug(f"DEBUG: Successfully read {request_count} ping-pong requests from {request_count_file}")
    # Format output as specified
    output = f"{timestamp}: {random_id}.\nPing / Pongs: {request_count}\n"
    logger.debug(f"DEBUG: Returning output:\n{output}")
    return output
