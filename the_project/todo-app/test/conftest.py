import pytest
#import asyncio
import subprocess
import time
import os
#from httpx import AsyncClient
#from main import app, ImageCache
import logging


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    logging.basicConfig(
        level=logging.DEBUG,  # or INFO for less verbosity
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger()
    logger.info("Logger configured for test session")
    yield logger
    # Optional: clean up or flush handlers if needed


@pytest.fixture(scope="session")
def fastapi_server(configure_logging):
    logger = configure_logging
    # Start app process with suitable port, e.g. 8000
    # proc = subprocess.Popen(
    #     ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "3000", "--log_level", "debug"],
    #     stdout=subprocess.PIPE, stderr=subprocess.PIPE
    # )
    # logger.debug(f"fastapi_server: Started FastAPI server with PID {proc.pid}")
    
    # Wait some time for server to start
    time.sleep(1)

    yield

    # Teardown: terminate the process after tests
    # logger.debug(f"fastapi_server: Terminating FastAPI server with PID {proc.pid}")
    # proc.terminate()
    # proc.wait()


# @pytest.fixture
# def event_loop():
#     """Create an instance of the default event loop for asyncio tests."""
#     logger.debug("CONFTEST:event_loop: Creating new event loop for tests")
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     logger.debug("CONFTEST:event_loop: Created new event loop for tests, yeilding")
#     yield loop
#     logger.debug("CONFTEST:event_loop: yield returned, Closing event loop after tests")
#     loop.close()

# @pytest.fixture
# async def async_client():
#     """Create an async HTTP client for testing FastAPI endpoints."""
#     logger.debug("CONFTEST:async_client: Creating AsyncClient for tests")
#     async with AsyncClient(app=app, base_url="http://testserver") as client:
#         logger.debug("CONFTEST:async_client: AsyncClient created, yeilding to test")
#         yield client
#         logger.debug("CONFTEST:async_client: yield returned, AsyncClient test complete")

# # # Fixture for a temporary cache directory
# # @pytest.fixture
# # def temp_cache_dir(tmp_path):
# #     logger.debug(f"CONFTEST:temp_cache_dir: Creating temporary cache directory for tests: {tmp_path}")
# #     return tmp_path

# @pytest.fixture
# def test_cache(tmp_path):
#     """
#     Create an ImageCache instance with a temporary cache directory,
#     allowing isolated file system cache for tests.
#     """
#     os.environ["CACHE_DIR"] = str(tmp_path)  # Override env var for test
#     logger.debug(f"CONFTEST:test_cache Creating ImageCache with cache dir: {tmp_path}")    
#     cache = ImageCache(cache_dir=str(tmp_path), ttl=2)  # short TTL for faster tests
#     return cache
