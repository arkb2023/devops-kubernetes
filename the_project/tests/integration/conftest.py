import subprocess
import time
import pytest

@pytest.fixture(scope="session")
def start_services():
    todo_backend_proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--log-level", "debug"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    todo_app_proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "3000", "--log-level", "debug"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for servers to be ready
    time.sleep(3)

    yield (todo_app_proc, todo_backend_proc)

    # Stop servers
    todo_app_proc.terminate()
    todo_backend_proc.terminate()

    try:
        todo_app_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        todo_app_proc.kill()

    try:
        todo_backend_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        todo_backend_proc.kill()

    # Capture logs for debugging
    stdout_app, stderr_app = todo_app_proc.communicate(timeout=1)
    stdout_backend, stderr_backend = todo_backend_proc.communicate(timeout=1)

    print("\n--- todo-app logs ---")
    print(stdout_app)
    print(stderr_app)

    print("\n--- todo-backend logs ---")
    print(stdout_backend)
    print(stderr_backend)
