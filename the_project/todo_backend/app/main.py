# FastAPI app initialization and router inclusion, configures middleware (e.g., CORS).
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import todos

app = FastAPI(title="Todo Backend")

# Allow CORS so frontend Todo app can call backend APIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust or restrict origins accordingly
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todos.router)


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
