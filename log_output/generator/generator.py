from fastapi import FastAPI
from datetime import datetime
import string
import random
import asyncio
import logging
import sys
import os

app = FastAPI()

# Configure logger once at module level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get log directory from environment variable, default to /tmp
LOG_DIR = os.getenv("LOG_DIR", "/usr/src/app/files")
LOG_FILE = os.path.join(LOG_DIR, "output.log")

# Generates a random string on startup and 
# writes a line with the random string and timestamp every 5 seconds into a file.

random_string = ''.join(random.choices(string.ascii_letters, k=10))

@app.on_event("startup")
async def startup_event():
    logger.debug(f"Startup event triggered with random_string: {random_string}")
    logger.debug(f"Log file path: {LOG_FILE}")
    asyncio.create_task(write_logs())
    logger.debug("write_logs task created")

async def write_logs():
    while True:
        try:
            logger.debug("Writing log entry")
            with open(LOG_FILE, 'a') as f:
                log_entry = f"{random_string} - {datetime.now()}\n"
                f.write(log_entry)
                logger.debug(f"Log written: {log_entry.strip()}")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error writing log: {e}")
            await asyncio.sleep(5)
