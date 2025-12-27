# greeter/app.py
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI()

VERSION = os.getenv("VERSION", "unknown")
MESSAGE = f"greetings: Hello from version {VERSION}"

@app.get("/", tags=["health"])
async def root():
    return {"message": MESSAGE}

@app.get("/greet", tags=["greeter"])
async def greet():
    return HTMLResponse(content=f"{MESSAGE}")

@app.get("/healthz", tags=["health"])
async def healthz():
    return {"status": "healthy", "version": VERSION}
