from fastapi import FastAPI
from contextlib import asynccontextmanager
from .storage import init_db, engine
from fastapi.middleware.cors import CORSMiddleware
from .routes import todos

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(title="Todo API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)
@app.get("/test")
async def test():
    return {"status": "ok"}
@app.get("/")
async def root():
    return {"message": "Todo API is running"}

# Run with: uvicorn app.main:app --reload

# Code files:
# app/
#   main.py
#   models.py: # Models: Todo defines the todo data schema.
# storage.py
# routes/todos.py
# models.py

# Supported Endpoints:
# GET /todos:
# Handler: app/routes/todos.py:get_todos
# Returns: app/storage.py:todo_list

# POST /todos:
# Handler: app/routes/todos.py:create_todo
# Input: Pydantic validates incoming todo JSON body against app/models.py:Todo
# Store:  Add todo to storage
#   Calls storage.py:add_todo to add new todo to in-memory list.
# Return: 201 Created JSON response on success.
