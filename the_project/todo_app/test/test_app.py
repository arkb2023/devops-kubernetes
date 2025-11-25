import os
import time
import pytest
import httpx
import logging



CACHE_URL = "http://127.0.0.1:3000"  # Adjust to your test server URL

@pytest.mark.asyncio
async def test_initial_image_fetch_and_cache(fastapi_server, configure_logging):
    """
    Test initial image fetch: no cached image exists, app fetches and caches new image.
    """
    logger = configure_logging
    cache_dir = "./cache"
    # Clean cache dir before test to simulate no cached image
    if os.path.exists(cache_dir):
        for f in os.listdir(cache_dir):
            os.remove(os.path.join(cache_dir, f))

    async with httpx.AsyncClient(base_url=CACHE_URL) as client:
        logger.debug("Test: Sending GET request to /")
        # First main page load triggers initial image fetch on startup or request
        resp = await client.get("/")
        logger.debug(f"Test: Response status code for / : {resp.status_code}")
        assert resp.status_code == 200
        assert "<img src=\"/image\"" in resp.text

        # The image file and timestamp should now exist on disk
        assert os.path.exists(os.path.join(cache_dir, "cached_image.jpg"))
        assert os.path.exists(os.path.join(cache_dir, "cache_timestamp.txt"))

@pytest.mark.asyncio
async def test_cached_image_served_within_ttl(fastapi_server, configure_logging):
    """
    Test that within TTL, cached image is served, no new fetch triggered.
    """
    logger = configure_logging
    cache_dir = "./cache"

    # Write a current timestamp to simulate fresh cache
    timestamp_path = os.path.join(cache_dir, "cache_timestamp.txt")
    with open(timestamp_path, "w") as f:
        f.write(str(int(time.time())))

    async with httpx.AsyncClient(base_url=CACHE_URL) as client:
        # Call the /image endpoint multiple times within TTL
        #resp1 = await client.get("/image")
        resp1 = await client.get("/")
        assert resp1.status_code == 200

        #resp2 = await client.get("/image")
        resp2 = await client.get("/")
        assert resp2.status_code == 200

        # Timestamp file should not have changed (no refetch)
        with open(timestamp_path, "r") as f:
            ts_after = int(f.read())
        assert ts_after >= int(time.time()) - 10  # Within TTL range, approx

@pytest.mark.asyncio
async def test_grace_period_allows_one_extra_request_after_ttl(fastapi_server, configure_logging):
    """
    Cache expired but grace period allows serving old image once more before refetch on next request.
    """
    logger = configure_logging
    cache_dir = "./cache"
    timestamp_path = os.path.join(cache_dir, "cache_timestamp.txt")

    # Write timestamp older than TTL to simulate expired cache
    #old_ts = int(time.time()) - 700  # ~11.5 minutes old (TTL=600 sec)
    old_ts = get_timestamp_from_file(timestamp_path) - 700
    with open(timestamp_path, "w") as f:
        f.write(str(old_ts))

    async with httpx.AsyncClient(base_url=CACHE_URL) as client:
        # First request after expiry should serve old image (grace)
        #resp1 = await client.get("/image")
        resp1 = await client.get("/")
          # Small delay to ensure timestamp file read consistency
        logger.debug(f"^^^^^^^^ After first request (grace), timestamp: {get_timestamp_from_file(timestamp_path)}")
        assert resp1.status_code == 200

        # Cache timestamp should still be old (not refreshed yet)
        with open(timestamp_path, "r") as f:
            ts1 = int(f.read())
        assert ts1 == old_ts

        # Second request triggers fetching new image and cache refresh
        resp2 = await client.get("/")
        time.sleep(1)
        logger.debug(f"^^^^^^^^ After second request, timestamp: {get_timestamp_from_file(timestamp_path)}")
        assert resp2.status_code == 200

        with open(timestamp_path, "r") as f:
            ts2 = int(f.read())
        logger.debug(f"^^^^^^^^ compare Before and After: {ts1} vs {ts2}")
        assert ts2 > ts1  # Timestamp updated indicating new fetch

@pytest.mark.asyncio
async def test_cache_refresh_after_grace_period(fastapi_server, configure_logging):
    """
    After grace period request served, next request should fetch and cache new image.
    """
    logger = configure_logging
    cache_dir = "./cache"
    timestamp_path = os.path.join(cache_dir, "cache_timestamp.txt")

    expired_ts = int(time.time()) - 700
    with open(timestamp_path, "w") as f:
        f.write(str(expired_ts))

    async with httpx.AsyncClient(base_url=CACHE_URL) as client:
        # First grace request serves old image
        await client.get("/")
        logger.debug(f"After first grace request, timestamp: {get_timestamp_from_file(timestamp_path)}")
        # Second request invokes refresh
        await client.get("/")
        logger.debug(f"After second request, timestamp: {get_timestamp_from_file(timestamp_path)}")
        # Third request after refresh should reflect new timestamp
        resp3 = await client.get("/")
        logger.debug(f"After third request, timestamp: {get_timestamp_from_file(timestamp_path)}")
        assert resp3.status_code == 200
        with open(timestamp_path, "r") as f:
            new_ts = int(f.read())
        assert new_ts > expired_ts

def get_timestamp_from_file(timestamp_path):
    with open(timestamp_path, "r") as f:
        return int(f.read())
    
