from fastapi import FastAPI
from datetime import datetime
import os
import logging

app = FastAPI()

# Configure logger once at module level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# read that file (/tmp/output.log written by ../generator/generator.py program 
# and provide the content in the HTTP GET endpoint for the user to see

log_dir = os.getenv("LOG_DIR", "/usr/src/app/files")
log_file = os.getenv("LOG_FILE", "output.log")
log_path = os.path.join(log_dir, log_file)

logger.debug(f"Log file path: {log_path}")

@app.get("/")
def get_logs():
    print(f"DEBUG: Request received at {datetime.now().isoformat()}")
    try:
        with open(log_path, "r") as f:
            content = f.read()
        print(f"DEBUG: Successfully read {len(content)} bytes from {log_path}")
        return content.splitlines()
    except FileNotFoundError:
        print(f"DEBUG: Log file not found at {log_path}")
        return {"error": "Log file not found"}
