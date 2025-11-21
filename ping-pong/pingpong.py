from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

class Counter:
    def __init__(self):
        self.counter = 0

    def incr(self):
        self.counter += 1
        return self.counter

app = FastAPI()
counter = Counter()

@app.get("/pingpong", response_class=PlainTextResponse)
def pingpong():
    return f"pong: {counter.incr()}"
