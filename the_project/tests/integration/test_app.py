import pytest
import httpx
from app.routes import frontend

TODO_APP_URL = "http://127.0.0.1:3000"
TODO_BACKEND_URL = "http://127.0.0.1:8000"

@pytest.mark.asyncio
async def test_create_and_list_todos(start_services):
    async with httpx.AsyncClient() as client:
        # Initially frontend loads page
        resp = await client.get(f"{TODO_APP_URL}/")
        assert resp.status_code == 200
        assert "<title>The Project App</title>" in resp.text

        # Initially backend todo list empty
        resp = await client.get(f"{TODO_BACKEND_URL}/todos")
        assert resp.status_code == 200
        assert resp.json() == []

        # Create a new todo via backend API
        new_todo = {"text": "Integration test todo"}
        resp = await client.post(f"{TODO_BACKEND_URL}/todos", json=new_todo)
        assert resp.status_code == 201

        # Backend todo list now contains the new todo
        resp = await client.get(f"{TODO_BACKEND_URL}/todos")
        todos = resp.json()
        assert any(t["text"] == new_todo["text"] for t in todos)
