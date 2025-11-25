import subprocess
import time
import requests
import pytest

BASE_URL = "http://127.0.0.1:8000"

@pytest.fixture(scope="module", autouse=True)
def todo_backend_server():
    # Start uvicorn server for todo-backend
    proc = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Wait for server to start listening
    time.sleep(2)

    yield  # Run tests

    # Teardown, stop server
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

def test_get_todos_empty():
    resp = requests.get(f"{BASE_URL}/todos")
    assert resp.status_code == 200
    assert resp.json() == []

def test_post_todo_and_get():
    new_todo = {"text": "Test todo item"}
    resp = requests.post(f"{BASE_URL}/todos", json=new_todo)
    assert resp.status_code == 201
    data = resp.json()
    assert data.get("message") == "Todo added successfully"

    resp2 = requests.get(f"{BASE_URL}/todos")
    todos = resp2.json()
    assert any(todo["text"] == new_todo["text"] for todo in todos)
