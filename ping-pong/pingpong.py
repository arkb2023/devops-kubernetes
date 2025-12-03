import os
import logging
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, select, update


# 1. CONFIGURE LOGGING FIRST
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"

# SUPPRESS NOISE 
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger("ping-pong")
logger.setLevel(logging.DEBUG)  # DEBUG for testing app


# Config from environment
POSTGRES_USER = os.getenv("POSTGRES_USER", "testdbuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "testdbuserpassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "testdb")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
logger.debug(f"Database URL: {DATABASE_URL}")

# Async SQLAlchemy setup - echo suppression
engine = create_async_engine(
    DATABASE_URL,
    echo=False,        # NO SQL noise
    echo_pool=False,   # NO pool noise
    future=True
)
logger.debug("Created async database engine")
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
logger.debug("Created async session maker")
Base = declarative_base()
logger.debug("Created declarative base")


# Model 
class PingPongCounter(Base):
    __tablename__ = "pingpong_counter"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)


app = FastAPI()


@app.on_event("startup")
async def startup():
    logger.info("Startup: creating DB schema if not exists")
    async with engine.begin() as conn:
        logger.debug("Creating all tables")
        await conn.run_sync(Base.metadata.create_all)
        logger.debug("Tables created")
    
    # Idempotent row creation Perfect
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PingPongCounter).where(PingPongCounter.id == 1))
        row = result.scalar_one_or_none()
        if row is None:
            logger.debug("Initializing pingpong_counter row id=1,value=0")
            session.add(PingPongCounter(id=1, value=0))
            await session.commit()
            logger.debug("Initialized row")


@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
    logger.info("Shutdown: closed DB engine")


@app.get("/pings")
async def get_pong_count():
    logger.debug("/pings - Starting")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PingPongCounter.value).where(PingPongCounter.id == 1))
        value = result.scalar()
        logger.debug(f"/pings - pong: {value}")
        #return {"pong": value}
        return PlainTextResponse(f"Ping / Pongs: {value}") 


@app.get("/pingpong")
async def pingpong():
    logger.debug("/pingpong - Starting")
    
    async with AsyncSessionLocal() as session:
        # READ
        result = await session.execute(select(PingPongCounter.value).where(PingPongCounter.id == 1))
        old_value = result.scalar()
        logger.debug(f"/pingpong - old: {old_value}")
        
        # UPDATE
        logger.debug(f"/pingpong - {old_value} → {old_value + 1}")
        await session.execute(
            update(PingPongCounter)
            .where(PingPongCounter.id == 1)
            .values(value=PingPongCounter.value + 1)
        )
        await session.commit()
        logger.debug("/pingpong - committed")
        
        # REFETCH Critical fix
        result = await session.execute(select(PingPongCounter.value).where(PingPongCounter.id == 1))
        new_value = result.scalar()
        logger.debug(f"/pingpong - new: {new_value}")
        
        logger.debug(f"/pingpong - returning {new_value}")
        #return {"pong": new_value}  # JSON response
        return PlainTextResponse(f"pong: {new_value}")


@app.get("/")
async def root():
    logger.debug("ping-pong: root endpoint")
    return {"message": "Ping-pong API v2.7.4 running"}
