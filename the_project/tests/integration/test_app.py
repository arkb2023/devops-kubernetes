import pytest
import httpx
from app.routes import frontend
import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)
logger.info(f"test_app.py module loaded: LOG_LEVEL={LOG_LEVEL}, LOG_FORMAT={LOG_FORMAT}")

TODO_APP_URL = os.getenv("TODO_APP_URL", "http://localhost:8080")
TODO_BACKEND_URL = os.getenv("TODO_BACKEND_URL", "http://localhost:8081")



@pytest.mark.asyncio
async def test_create_and_list_todos(start_services):
    async with httpx.AsyncClient() as client:
        # Initially frontend loads page
        logger.info(f"Testing main page load from {TODO_APP_URL}/")
        resp = await client.get(f"{TODO_APP_URL}/")
        logger.info(f"Main page response status: {resp.status_code}")
        assert resp.status_code == 200
        logger.info(f"Main page response text: {resp.text[:100]}...")  # Log first 100 chars
        response_text = "<title>The Project App</title>"
        assert response_text in resp.text
        logger.info("Frontend Main page loaded successfully")

        # Initially backend todo list empty
        logger.info(f"Testing initial todo list from {TODO_BACKEND_URL}/todos")
        resp = await client.get(f"{TODO_BACKEND_URL}/todos")
        logger.info(f"Initial todo list response status: {resp.status_code}")
        assert resp.status_code == 200
        logger.info(f"Initial todo list response JSON: {resp.json()}")
        assert resp.json() == []
        logger.info("Backend initial todo list is empty as expected")

        # Create a new todo via backend API
        logger.info(f"Creating new todo via {TODO_BACKEND_URL}/todos")
        new_todo = {"text": "Integration test todo"}
        logger.info(f"New todo payload: {new_todo}")
        resp = await client.post(f"{TODO_BACKEND_URL}/todos", json=new_todo)
        logger.info(f"Create todo response status: {resp.status_code}")
        assert resp.status_code == 201
        logger.info(f"Create todo response JSON: {resp.json()}")
        assert resp.json() == {"message": "Todo added successfully"}
        logger.info("New todo created successfully via backend API")

        # Backend todo list now contains the new todo
        logger.info(f"Verifying todo list from {TODO_BACKEND_URL}/todos after addition")
        resp = await client.get(f"{TODO_BACKEND_URL}/todos")
        logger.info(f"Todo list response status: {resp.status_code}")
        assert resp.status_code == 200
        logger.info(f"Todo list response JSON: {resp.json()}")
        todos = resp.json()
        logger.info(f"Current todos: {todos}")
        assert any(t["text"] == new_todo["text"] for t in todos)
        logger.info("Backend todo list contains the newly added todo")
