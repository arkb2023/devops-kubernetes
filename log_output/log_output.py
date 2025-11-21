from fastapi import FastAPI
from datetime import datetime
import string
import random

app = FastAPI()

# Generate a random string at startup and store the timestamp
startup_time = datetime.utcnow().isoformat()
random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

@app.get("/status")
def get_status():
    return {
        "startup_time": startup_time,
        "random_string": random_string
    }
