import os
import logging
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, select, update

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Config from environment
DB_USER = os.getenv("DB_USER", "testdbuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "testdbuserpassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "testdb")
PGDATA = os.getenv("PGDATA", "/data/pgdata")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
logger.debug(f"Database URL: {DATABASE_URL}")
# Async SQLAlchemy setup
engine = create_async_engine(DATABASE_URL, echo=True)
logger.debug("Created async database engine {engine}")
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
logger.debug("Created async session maker {AsyncSessionLocal}")
Base = declarative_base()
logger.debug("Created declarative base {Base}")

# Model definition
class PingPongCounter(Base):
    __tablename__ = "pingpong_counter"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)

app = FastAPI()

@app.on_event("startup")
async def startup():
    logger.info("Startup: creating DB schema if not exists")
    async with engine.begin() as conn:
        logger.debug("Creating all tables in the database")
        await conn.run_sync(Base.metadata.create_all)
        logger.debug("Ensured all tables are created")
    # Ensure row with id=1 exists
    async with AsyncSessionLocal() as session:
        logger.debug("Checking for existing pingpong_counter row with id=1")
        result = await session.execute(select(PingPongCounter).where(PingPongCounter.id == 1))
        logger.debug("Executed select query for pingpong_counter with id=1: {result}")
        row = result.scalar_one_or_none()
        logger.debug(f"Query result for pingpong_counter with id=1: {row}")
        if row is None:
            logger.debug("No existing row found, initializing pingpong_counter row with id=1 and value=0")
            session.add(PingPongCounter(id=1, value=0))
            await session.commit()
            logger.debug("Initialized pingpong_counter row with id=1 and value=0")

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
    logger.info("Shutdown: closed DB engine")

@app.get("/pings")
async def get_pong_count():
    logger.debug("Handling /pings request")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PingPongCounter.value).where(PingPongCounter.id == 1))
        logger.debug("Executed select query for pingpong_counter value with id=1: {result}")
        value = result.scalar_one_or_none() or 0
    return PlainTextResponse(f"Ping / Pongs: {value}")

@app.get("/pingpong", response_class=PlainTextResponse)
async def pingpong():
    logger.debug("Handling /pingpong request")
    async with AsyncSessionLocal() as session:
        # Atomic increment
        await session.execute(
            update(PingPongCounter)
            .where(PingPongCounter.id == 1)
            .values(value=PingPongCounter.value + 1)
        )
        await session.commit()
        logger.debug("Incremented pingpong_counter value for id=1")
        # Get updated value
        result = await session.execute(select(PingPongCounter.value).where(PingPongCounter.id == 1))
        value = result.scalar_one_or_none() or 0
    return f"pong: {value}\n"
