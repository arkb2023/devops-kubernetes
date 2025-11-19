from fastapi import FastAPI
import os

app = FastAPI()

PORT = os.environ.get("PORT", "8000")

@app.get("/")
def read_root():
    return {"message": f"Server started in port {PORT}"}
