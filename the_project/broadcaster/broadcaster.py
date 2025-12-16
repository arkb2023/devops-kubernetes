import os
import asyncio
import json
import nats
import aiohttp
import logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger("broadcaster")

DEFAULT_NATS_URL="nats://127.0.0.1:4222"

async def message_handler(msg: nats.aio.client.Msg):
    try:
        data_str = msg.data.decode("utf-8")
    except UnicodeDecodeError:
        data_str = repr(msg.data)

    logger.info(f"[broadcaster] subject={msg.subject} data={data_str}")

    if slack_webhook_url:
        # Include the full JSON payload in the Slack message
        text = f"Todo event on {msg.subject}:\n{data_str}"
        async with aiohttp.ClientSession() as session:
            await session.post(slack_webhook_url, json={"text": text})


async def main(slack_webhook_url, nats_url, subject="todos.>"):
    # Connect to NATS
    nc = await nats.connect(servers=[nats_url])
    logger.info(f"Connected to NATS at {nats_url}, subscribing to {subject}")

    # Async subscription with wildcard
    # every subscriber gets every matching message
    # await nc.subscribe(subject, cb=message_handler)

    # Queue group name (all replicas must use the same one)
    QUEUE_GROUP = "broadcaster-workers"
    # Use queue subscribe instead of plain subscribe
    await nc.subscribe(subject, queue=QUEUE_GROUP, cb=message_handler)
    
    # Keep running forever
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await nc.drain()

if __name__ == "__main__":
    try:
        slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", None)
        if not slack_webhook_url:
            logger.error(f"Slack Webhook URL unspecified")
            exit(1)

        nats_url = os.getenv("NATS_URL", DEFAULT_NATS_URL)
        logger.info(f"Using NATS_URL={nats_url}")

        asyncio.run(main(slack_webhook_url, nats_url=nats_url))
    except KeyboardInterrupt:
        logger.info("broadcaster shutting down...")