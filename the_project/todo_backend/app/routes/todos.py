from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..models import TodoCreate, TodoResponse, TodoUpdate, MessageResponse
from ..storage import (
    get_todos, create_todo, get_todo, update_todo, delete_todo, get_db_session
)
import logging
import os

logger = logging.getLogger("todo_backend") 

# This inherits main.py's configuration automatically:
# Level: INFO (from main.py basicConfig)
# Format: %(asctime)s [%(name)s] %(levelname)s %(message)s (from main.py)
# Handlers: stdout (from main.py)

router = APIRouter(prefix="/todos", tags=["todos"])

@router.get("/healthz")
async def healthz(db: AsyncSession = Depends(get_db_session)):
    try:
        await db.execute(text("SELECT 1"))
        logger.debug("healthz: todo backend db connection responsive")
        return {"status": "healthzy"}
    except Exception as e:
        logger.error(f"healthz DB error: {e}")
        raise HTTPException(503, "Todo DB not ready")

@router.get("/", response_model=List[TodoResponse])
async def get_todos_route(db: AsyncSession = Depends(get_db_session)):
    """Get all todos."""
    return await get_todos(db)

@router.post("/", response_model=TodoResponse, status_code=201)
async def create_todo_route(
    request: Request,  # Add Request for logging,
    todo: TodoCreate, 
    db: AsyncSession = Depends(get_db_session)
):
    """Create new todo."""
    logger.info(f"todos.py:create_todo_route called*****")
    
    # Log EVERY incoming POST /todos request
    logger.info(
        "todo_request_received",
        extra={
            "endpoint": "/todos",
            "method": "POST",
            "client_ip": request.client.host,
            "text_preview": todo.text[:50] + "..." if len(todo.text) > 50 else todo.text,
            "text_length": len(todo.text),
            "status": "received"
        }
    )

    result = await create_todo(db, todo)
    
    # Log SUCCESS
    logger.info(
        "todo_created_success",
        extra={
            "endpoint": "/todos",
            "todo_id": result.id,
            "text_preview": todo.text[:50] + "...",
            "text_length": len(todo.text),
            "status": "success"
        }
    )
    
    return result
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
    