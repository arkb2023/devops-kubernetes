# app/nats_client.py
import os
import json
import nats
import logging
from .models import TodoResponse

#logger = logging.getLogger("todo_nats")
logger = logging.getLogger("todo_backend")

NATS_URL = os.getenv("NATS_URL", "nats://127.0.0.1:4222")
NATS_SUBJECT_CREATED = "todos.created"
NATS_SUBJECT_UPDATED = "todos.updated"

# Simple, connect-per-publish POC
async def publish_todo_event(subject: str, payload: dict):
    try:
        logger.info(f"Connecting to NATS at {NATS_URL}")
        nc = await nats.connect(servers=[NATS_URL])
        payload_bytes = json.dumps(payload, default=str).encode("utf-8")
        await nc.publish(subject, payload_bytes)
        #await nc.publish(subject, json.dumps(payload).encode("utf-8"))
        await nc.drain()
        logger.info(f"Published to NATS {subject}: {payload}")
    except Exception as e:
        logger.error(f"Failed to publish to NATS: {e}")

