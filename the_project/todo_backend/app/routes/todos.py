# Implements API endpoints:
# GET /todos returns current todo list.
# POST /todos accepts new todo, validates input, adds to storage.
from fastapi import APIRouter, HTTPException
from typing import List
from app.models import Todo
from app.storage import todo_list, add_todo
import logging
import os
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.info(f"todos.py module loaded: LOG_LEVEL={LOG_LEVEL}, LOG_FORMAT={LOG_FORMAT}")

router = APIRouter()

@router.get("/todos", response_model=List[Todo])
async def get_todos():
    # Return the current list of todos
    # app/storage.py:todo_list
    # holds the current in-memory list of todos.
    # Returns the JSON serialized list of todos as response payload.
    logger.info("get_todos endpoint: Returning current todo list")
    return todo_list

@router.post("/todos", status_code=201)
async def create_todo(todo: Todo):
    # 1. FastAPI automatically parses and validates the incoming JSON body payload against 
    #    the Todo Pydantic model (app/models.py).
    # 2. If validation passes (todo text length between 1-140 chars), 
    #    this validated todo object is passed to the create_todo handler.
    # 3. Calls add_todo(todo) method in app/storage.py, 
    #    which appends the new todo item into the todo_list in-memory list.
    logger.info(f"create_todo endpoint: Adding new todo: {todo}")
    add_todo(todo)
    # Returns an HTTP 201 Created response with a success message.
    return {"message": "Todo added successfully"}
