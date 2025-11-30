import subprocess
import time
import pytest
import os
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

#logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
#logger = logging.getLogger(__name__)
logger = logging.getLogger("uvicorn")
logger.setLevel(LOG_LEVEL.upper())
logger.info(f"conftest.py module loaded: LOG_LEVEL={LOG_LEVEL}, LOG_FORMAT={LOG_FORMAT}")

@pytest.fixture(scope="session")
def start_services():
    todo_backend_port = os.getenv("TODO_BACKEND_PORT", "8080")
    todo_backend_host = os.getenv("TODO_BACKEND_HOST", "localhost")
    logging_level = os.getenv("LOG_LEVEL", "debug")
    project_root = os.getenv("THE_PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
    #logging.getLogger("uvicorn").setLevel(logging_level.upper())

    logger.info(f"Starting todo-backend on {todo_backend_host}:{todo_backend_port} with LOG_LEVEL={logging_level}")
    logger.info(f"BACKEND: uvicorn app.main:app --host {todo_backend_host} --port {todo_backend_port} --log-level {logging_level.lower()}")

    os.chdir(os.path.join(project_root, "./todo_backend"))
    logger.info(f"Changed working directory to todo_backend: {os.getcwd()}")
    todo_backend_proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", todo_backend_host, "--port", todo_backend_port, "--log-level", logging_level.lower()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for servers to be ready
    time.sleep(3)

    logger.info("Both services started, yielding control to tests")
    yield (todo_backend_proc)
    logger.info("Tests completed, shutting down services")
    # Stop servers

    todo_backend_proc.terminate()
#uvicorn app.main:app --host 127.0.0.1 --port 3001 --log-level debug 
#uvicorn app.main:app --host 127.0.0.1 --port 3000 --log-level debug
    try:
        todo_backend_proc.wait(timeout=5)
        logger.info("todo-backend terminated gracefully")
    except subprocess.TimeoutExpired:
        logger.warning("todo-backend did not terminate in time, killing process")
        todo_backend_proc.kill()

    # Capture logs for debugging
    stdout_backend, stderr_backend = todo_backend_proc.communicate(timeout=1)

    logger.info("\n--- todo-backend logs ---")
    print(stdout_backend)
    print(stderr_backend)
    logger.info ("Service shutdown complete")