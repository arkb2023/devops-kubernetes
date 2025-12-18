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

async def message_handler(msg: nats.aio.client.Msg, slack_webhook_url=None):
    
    try:
        data_str = msg.data.decode("utf-8")
    except UnicodeDecodeError:
        data_str = repr(msg.data)

    # Always logs
    logger.info(f"[broadcaster] subject={msg.subject} data={data_str}")

    if slack_webhook_url:
        # Include the full JSON payload in the Slack message
        text = f"Todo event on {msg.subject}:\n{data_str}"
        async with aiohttp.ClientSession() as session:
            await session.post(slack_webhook_url, json={"text": text})


async def main(slack_webhook_url=None, nats_url=None, subject="todos.>"):
    # Connect to NATS
    nc = await nats.connect(servers=[nats_url])
    logger.info(f"Connected to NATS at {nats_url}, subscribing to {subject}")

    # Async subscription with wildcard
    # every subscriber gets every matching message
    # await nc.subscribe(subject, cb=message_handler)

    # Queue group name (all replicas must use the same one)
    QUEUE_GROUP = "broadcaster-workers"
    # Use queue subscribe instead of plain subscribe
    # Pass slack_webhook_url via closure to async handler
    async def nats_handler(msg):
        await message_handler(msg, slack_webhook_url)
    await nc.subscribe(subject, queue=QUEUE_GROUP, cb=nats_handler)
    #await nc.subscribe(subject, queue=QUEUE_GROUP, cb=message_handler)
    
    # Keep running forever
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await nc.drain()

if __name__ == "__main__":
    try:
        nats_url = os.getenv("NATS_URL", DEFAULT_NATS_URL)
        logger.info(f"Using NATS_URL={nats_url}")
        
        is_fwd_to_external_svc = os.getenv("FORWARD_TO_EXTERNAL_SERVICE", "false")
        if is_fwd_to_external_svc == "true":
            # Production deployment
            logger.info("Production: Forwarding to Slack")
            slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
            if not slack_webhook_url:
                logger.error(f"SLACK_WEBHOOK_URL required")
                raise
        else: # Staging deployment
            logger.info("Staging: Logging only")
            slack_webhook_url = None

        asyncio.run(main(slack_webhook_url=slack_webhook_url, nats_url=nats_url))
    except KeyboardInterrupt:
        logger.info("broadcaster shutting down...")
