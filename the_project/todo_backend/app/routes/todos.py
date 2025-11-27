from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import TodoCreate, TodoResponse, TodoUpdate, MessageResponse
from ..storage import (
    get_todos, create_todo, get_todo, update_todo, delete_todo, get_db_session
)
import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.info(f"todos.py module loaded: LOG_LEVEL={LOG_LEVEL}")

router = APIRouter(prefix="/todos", tags=["todos"])

@router.get("/", response_model=List[TodoResponse])
async def get_todos_route(db: AsyncSession = Depends(get_db_session)):
    """Get all todos."""
    return await get_todos(db)

@router.post("/", response_model=TodoResponse, status_code=201)
async def create_todo_route(todo: TodoCreate, db: AsyncSession = Depends(get_db_session)):
    """Create new todo."""
    return await create_todo(db, todo)

@router.get("/{todo_id}", response_model=TodoResponse)
async def get_todo_route(todo_id: int, db: AsyncSession = Depends(get_db_session)):
    """Get single todo."""
    try:
        return await get_todo(db, todo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo_route(todo_id: int, update_data: TodoUpdate, db: AsyncSession = Depends(get_db_session)):
    """Update todo."""
    try:
        return await update_todo(db, todo_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{todo_id}", response_model=MessageResponse)
async def delete_todo_route(todo_id: int, db: AsyncSession = Depends(get_db_session)):
    """Delete todo."""
    if await delete_todo(db, todo_id):
        return {"message": f"Todo {todo_id} deleted successfully"}
    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")
    