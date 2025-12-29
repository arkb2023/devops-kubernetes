import os
import logging
import asyncio
import math
import random
import threading
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, select, update, text
from sqlalchemy.exc import OperationalError, ProgrammingError, NoResultFound

# 1. CONFIGURE LOGGING FIRST
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"

logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger("ping-pong")
logger.setLevel(logging.DEBUG)

# Config from environment
POSTGRES_USER = os.getenv("POSTGRES_USER", "testdbuser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "testdbuserpassword")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "testdb")
PORT = os.getenv("PORT", "0000")
knative = os.getenv("KNATIVE", "false")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{POSTGRES_DB}"
logger.debug(f"Database URL: {DATABASE_URL}")
logger.debug(f"Listening Port: {PORT}")
logger.debug(f"Knative: {knative}")


# Async SQLAlchemy setup
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    echo_pool=False,
    future=True,
    pool_pre_ping=True,  #  Validate connections
    pool_recycle=300     #  Recycle stale connections
)
logger.debug("Created async database engine")
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

# Model 
class PingPongCounter(Base):
    __tablename__ = "pingpong_counter"
    id = Column(Integer, primary_key=True)
    value = Column(Integer, nullable=False)

app = FastAPI()

def cpu_burner():
    """
    Periodically burns CPU in a tight loop.
    Adjust burn/rest durations to control how aggressive it is.
    """
    while True:
        # Burn for 5 seconds
        end = time.time() + 5
        while time.time() < end:
            # Some meaningless CPU work
            math.sqrt(random.random())

        # Rest for 5 seconds
        time.sleep(5)



#  PRODUCTION: Robust DB Self-Healing Startup
@app.on_event("startup")
async def startup():
    logger.info("Startup: Self-healing database initialization...")

    # Start CPU burner if enabled
    ENABLE_CPU_STRESS = os.getenv("ENABLE_CPU_STRESS", "false").lower() == "true"
    if ENABLE_CPU_STRESS:
        logger.warning("CPU stress mode ENABLED for this instance")
        threading.Thread(target=cpu_burner, daemon=True).start()

    max_retries = 30  # 5 minutes max
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                # Test connection + create table
                # 1. Checks if pingpong_counter table exists
                # 2. If MISSING → CREATE TABLE pingpong_counter (id, value)
                # 3. If EXISTS → Does nothing (idempotent)
                # 
                # SQLAlchemy scans your models (PingPongCounter)
                #   generates DDL
                #   runs CREATE TABLE IF NOT EXISTS automatically.
                # Workflow:
                #   Pod starts
                #   FastAPI startup()
                #   DB connect
                #   Table missing?
                #       Base.metadata.create_all() → CREATE TABLE 
                #   Row missing?
                #       INSERT id=1,value=0 
                logger.debug(f"Attempt {attempt + 1}/{max_retries}: Creating schema...")
                # 1. CREATE TABLE (always idempotent)
                await conn.run_sync(Base.metadata.create_all)
                logger.debug("Tables created")

                # Idempotent row creation
                # 2. CHECK/INSERT ROW (raw SQL)
                result = await conn.execute(
                    text("SELECT value FROM pingpong_counter WHERE id = 1")
                )
                existing_value = result.scalar()
                
                if existing_value is None:
                    logger.info("Initializing pingpong_counter row id=1,value=0")
                    await conn.execute(
                        text("INSERT INTO pingpong_counter (id, value) VALUES (1, 0)")
                    )
                    logger.info("Row initialized")
                else:
                    logger.debug(f"Row exists: id=1, value={existing_value}")
                
                await conn.commit()
                logger.info("Database fully self-healed and ready!")
                return
                
        except (OperationalError, ProgrammingError) as e:
            logger.warning(f"DB not ready (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logger.error("DB startup failed after all retries")
                raise
        except Exception as e:
            #logger.error(f"Unexpected error during startup: {e}")
            #raise
            logger.warning(f"DB not ready yet, will retry: {e}")
            await asyncio.sleep(retry_delay)

@app.on_event("shutdown")
async def shutdown():
    await engine.dispose()
    logger.info("Shutdown: closed DB engine")

@app.get("/pings")
async def get_pong_count():
    logger.debug("/pings - Starting")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PingPongCounter.value).where(PingPongCounter.id == 1)
            )
            value = result.scalar()
            if value is None:
                raise HTTPException(status_code=500, detail="Counter not initialized")
            logger.debug(f"/pings - pong: {value}")
            if knative.lower() == "true":
                resp_str = f"[Knative] Ping / Pongs: {value}"
            else:
                resp_str = f"Ping / Pongs: {value}"

            return PlainTextResponse(resp_str)
    except Exception as e:
        logger.error(f"/pings error: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

# Exercise 3.4: Root path rewrite: changed to '/'
# @app.get("/")
# Exercise 5.3: istio httproute: changed to /pingpong
@app.get("/pingpong")
async def pingpong():
    logger.debug("Entered pingpong route handler")
    try:
        async with AsyncSessionLocal() as session:
            # READ current value
            result = await session.execute(
                select(PingPongCounter.value).where(PingPongCounter.id == 1)
            )
            old_value = result.scalar()
            logger.debug(f"pingpong - old: {old_value}")
            
            if old_value is None:
                logger.warning("Counter row missing - initializing")
                await session.execute(
                    text("INSERT INTO pingpong_counter (id, value) VALUES (1, 0)")
                )
                await session.commit()
                old_value = 0
            
            # UPDATE
            logger.debug(f"pingpong - {old_value} → {old_value + 1}")
            await session.execute(
                update(PingPongCounter)
                .where(PingPongCounter.id == 1)
                .values(value=PingPongCounter.value + 1)
            )
            await session.commit()
            
            # REFETCH (critical for transaction visibility)
            result = await session.execute(
                select(PingPongCounter.value).where(PingPongCounter.id == 1)
            )
            new_value = result.scalar()
            logger.debug(f"pingpong - new: {new_value}")
            
            if knative.lower() == "true":
                resp_str = f"[Knative] pong: {new_value}"
            else:
                resp_str = f"pong: {new_value}"
            
            return PlainTextResponse(resp_str)
            
    except Exception as e:
        logger.error(f"pingpong error: {e}")
        raise HTTPException(status_code=503, detail="Database operation failed")

@app.get("/healthz")
async def healthz():
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            logger.debug("healthz: db connection responsive")
        return {"status": "healthzy"}
    except Exception as e:
        logger.error(f"healthz DB error: {e!r}")
        raise HTTPException(503, "DB not ready")
