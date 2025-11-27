import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
from .models import Base, TodoDB, TodoCreate, TodoResponse, TodoUpdate

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)




def get_required_env(var_name: str, default: str = None) -> str:
    """Check if env var exists, log status, return value or default"""
    if var_name in os.environ:
        value = os.environ[var_name]
        logger.info(f"✅ {var_name}={value}")
        return value
    else:
        logger.warning(f"❌ {var_name} MISSING - using default: {default}")
        return default or ""

# Usage in your storage.py
DB_HOST = get_required_env("DB_HOST", "undefined")
DB_PORT = int(get_required_env("DB_PORT", "1111"))
POSTGRES_DB = get_required_env("POSTGRES_DB", "undefined")
POSTGRES_USER = get_required_env("POSTGRES_USER", "undefined")
POSTGRES_PASSWORD = get_required_env("POSTGRES_PASSWORD")  # No default - will be empty!

logger.info(f"Final DB URL:postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}")

# Database config from env vars (Kubernetes ConfigMap/Secret)
# DB_HOST = os.getenv("DB_HOST", "localhost")
# DB_PORT = int(os.getenv("DB_PORT", "5432"))
# POSTGRES_DB = os.getenv("POSTGRES_DB", "tododb")
# POSTGRES_USER = os.getenv("POSTGRES_USER", "testdbuser")
# POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "testdbuserassword")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"

logger.info(f"DATABASE_URL {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=True)
logger.info(f"engine: {engine}")
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    """Create tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_todos(db: AsyncSession) -> list[TodoResponse]:
    result = await db.execute(select(TodoDB).order_by(TodoDB.created_at.desc()))
    todos = result.scalars().all()
    return [TodoResponse.model_validate(todo) for todo in todos]

async def create_todo(db: AsyncSession, todo: TodoCreate) -> TodoResponse:
    db_todo = TodoDB(text=todo.text)
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return TodoResponse.model_validate(db_todo)

async def get_todo(db: AsyncSession, todo_id: int) -> TodoResponse:
    result = await db.execute(select(TodoDB).where(TodoDB.id == todo_id))
    todo = result.scalar_one_or_none()
    if not todo:
        raise ValueError(f"Todo {todo_id} not found")
    return TodoResponse.model_validate(todo)

async def update_todo(db: AsyncSession, todo_id: int, update_data: TodoUpdate) -> TodoResponse:
    todo = await get_todo(db, todo_id)
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(todo, field, value)
    await db.commit()
    await db.refresh(todo)
    return TodoResponse.model_validate(todo)

async def delete_todo(db: AsyncSession, todo_id: int) -> bool:
    result = await db.execute(select(TodoDB).where(TodoDB.id == todo_id))
    todo = result.scalar_one_or_none()
    if not todo:
        return False
    await db.delete(todo)
    await db.commit()
    return True
