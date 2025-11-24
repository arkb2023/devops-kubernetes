import os
import time
import logging
import aiohttp
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager

logging.basicConfig(
  level=logging.DEBUG,
  # Enable INFO in deployment
  # level=logging.INFO,  
  format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ImageCache:
  def __init__(self, cache_dir: str = "./cache", ttl: int = 600):
    self.cache_dir = cache_dir
    self.ttl = ttl
    self.image_path = os.path.join(cache_dir, "cached_image.jpg")
    self.timestamp_path = os.path.join(cache_dir, "cache_timestamp.txt")
    self.grace_period_used = False
    logger.debug(f"ImageCache initialized with cache_dir: {cache_dir}, ttl: {ttl}s")
    os.makedirs(cache_dir, exist_ok=True)

  async def fetch_and_cache_image(self) -> bool:
    """Fetch a random image and cache it locally."""
    logger.debug("Fetching new image from external source")
    img_url = "https://picsum.photos/500"
    try:
      async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as resp:
          if resp.status == 200:
            img_bytes = await resp.read()
            timestamp_str = str(int(time.time()))
            with open(self.image_path, "wb") as f:
              f.write(img_bytes)
            with open(self.timestamp_path, "w") as f:
              #f.write(str(int(time.time())))
              f.write(timestamp_str)
            logger.debug(f"Image fetched and cached successfully: timestamp {timestamp_str}")
            self.grace_period_used = False
            return True
    except Exception as e:
      logger.error(f"Failed to fetch image: {e}")
    return False

  def is_cache_expired(self) -> bool:
    """Check if cache is expired or missing."""
    if not os.path.exists(self.image_path) or not os.path.exists(self.timestamp_path):
      logger.debug("Cache expired: Missing image or timestamp file")
      return True
    
    with open(self.timestamp_path, "r") as f:
      cached_time = int(f.read())
    
    age = int(time.time()) - cached_time
    logger.debug(f"Cache age: {age}s, TTL: {self.ttl}s, Expired: {age > self.ttl}")
    return age > self.ttl

  # Add method to reset grace period for clarity and potential use
  def reset_grace_period(self):
      self.grace_period_used = False
      
async def lifespan(app: FastAPI):
    """Fetch image on startup if cache is expired."""
    global cache

    # Use explicit environment variable default inline
    cache_dir = os.getenv("CACHE_DIR", "./cache")
    cache = ImageCache(cache_dir=cache_dir, ttl=600)
    # startup logic here
    logger.debug("Lifespan startup: Checking cache status")
    if cache.is_cache_expired():
        logger.debug("Lifespan startup: Cache is expired on startup, fetching new image")
        await cache.fetch_and_cache_image()
        logger.debug("Lifespan startup: Image fetched on startup")
    yield
    # TODO: shutdown logic here
    logger.debug("Lifespan shutdown: Application is shutting down")

# Cache global is optional but good to explicitly declare
cache: ImageCache | None = None  # type hint for clarity (Python 3.10+)

logger.debug(f"Setting up FastAPI app with lifespan")
app = FastAPI(lifespan=lifespan)
logger.debug(f"FastAPI app setup complete")

@app.get("/", response_class=HTMLResponse)
async def main_page():
  """Main page that serves the cached image."""
  # Consider adding error handling in routes where cache is None
  if cache is None:
    raise HTTPException(status_code=500, detail="Cache not initialized")
  
  if cache.is_cache_expired():
    logger.debug("main_page endpoint: Cache is expired")
    if not cache.grace_period_used and os.path.exists(cache.image_path):
      logger.debug("main_page endpoint: Serving cached image under grace period")
      cache.grace_period_used = True
    else:
      logger.debug("main_page endpoint: Fetching new image as grace period used or no cached image")
      await cache.fetch_and_cache_image()

  html_content = """
  <html>
  <head><title>The Project App</title></head>
  <body>
  <h1>The Project App</h1>
  <hr/>
  <img src="/image" alt="Random Image"/>
  <hr/>
  <p>DevOps with Kubernetes 2025</p>
  </body>
  </html>
  """
  return HTMLResponse(content=html_content)

@app.get("/image")
async def get_image():
  if cache is None or not os.path.exists(cache.image_path):
      raise HTTPException(status_code=404, detail="Image not available")
  return FileResponse(cache.image_path, media_type="image/jpeg")
  
