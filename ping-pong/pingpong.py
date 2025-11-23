from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from datetime import datetime
import string
import random
import asyncio
import logging
import sys
import os

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

    
app = FastAPI()
# Configure logger once at module level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
# Get log directory from environment variable, default to "/usr/src/app/files"
shared_dir = os.getenv("LOG_DIR", "/usr/src/app/files")
request_count_file = os.path.join(shared_dir, "pingpong-requests.txt")
counter = Counter()

@app.get("/pingpong", response_class=PlainTextResponse)
async def pingpong():
    # Increment and write the pingpong request count
    request_count = counter.incr()
    asyncio.create_task(write_logs(request_count))
    return f"pong: {request_count}\n"

@app.on_event("startup")
async def startup_event():
    logger.debug(f"Startup event: Log file path: {request_count_file}")

    # if file exists, 
    #   read the existing count
    #   set the counter object to that count,
    #   nothing to write in the file
    # if not, 
    #   create the file, 
    #   set the counter object to 0,
    #   write counter in the file
    if os.path.exists(request_count_file):
        try:
            with open(request_count_file, 'r') as f:
                content = f.read().strip()
                request_count = int(content)
                counter.set(request_count)
                logger.debug(f"Read existing pingpong request count: {request_count}")
        except Exception as e:
            logger.error(f"Error reading pingpong request count file: {e}")
    else:
        logger.debug("Pingpong file does not exist. Starting from 0.")
        counter.set(0)
        # Initial value write
        asyncio.create_task(write_logs(counter.get()))
        logger.debug("Startup event: processing completed.")

async def write_logs(counter_value):
    try:
        logger.debug(f"Writing pingpong request count: {counter_value}")
        with open(request_count_file, 'w') as f:
            request_count = str(counter_value)
            f.write(request_count)
            logger.debug(f"Pingpong request count written: {request_count}")
    except Exception as e:
        logger.error(f"Error writing pingpong request count: {e}")
