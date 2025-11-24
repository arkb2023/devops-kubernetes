import os
import time
import logging
import aiohttp
import asyncio
import json
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
      self.metadata_path = os.path.join(cache_dir, "cache_metadata.json")
      self.grace_period_used = False
      self.access_count = 0 # total access count
      self.image_access_count = 0 # per image access count
      self.last_access_time = None
      self.download_timestamp = None  # Timestamp of image fetch
      os.makedirs(cache_dir, exist_ok=True)
      self._load_metadata()
      logger.debug(f"ImageCache initialized with cache_dir: {cache_dir}, ttl: {ttl}s")

  def _load_metadata(self):
      if os.path.exists(self.metadata_path):
          logger.debug(f"Loading metadata from {self.metadata_path}")
          try:
              with open(self.metadata_path, "r") as f:
                  data = json.load(f)
              self.grace_period_used = data.get("grace_period_used", False)
              self.access_count = data.get("access_count", 0)
              self.last_access_time = data.get("last_access_time", None)
              self.download_timestamp = data.get("download_timestamp", None)
              self.image_access_count = data.get("image_access_count", 0)
              logger.debug(f"Loaded metadata: {data}")

          except Exception as e:
              logger.error(f"Failed to load cache metadata: {e}")
              self._reset_metadata()
      else:
          logger.debug(f"No metadata file found at {self.metadata_path}, initializing defaults")
          self._reset_metadata()

  def _reset_metadata(self):
      self.grace_period_used = False
      self.access_count = 0
      self.last_access_time = None
      self.download_timestamp = None
      self.image_access_count = 0
      self._save_metadata()

  def _save_metadata(self):
      data = {
          "grace_period_used": self.grace_period_used,
          "access_count": self.access_count,
          "last_access_time": self.last_access_time,
          "download_timestamp": self.download_timestamp,
          "image_access_count": self.image_access_count,
      }
      try:
          with open(self.metadata_path, "w") as f:
              json.dump(data, f)
      except Exception as e:
          print(f"Failed to save cache metadata: {e}")

  def record_access(self):
      self.access_count += 1
      self.image_access_count += 1
      self.last_access_time = time.time()
      self._save_metadata()

  
  def is_cache_expired(self) -> bool:
      """Check if cache is expired or missing."""
      if not os.path.exists(self.image_path) or self.download_timestamp is None:
        logger.debug("Cache expired: Missing image or download timestamp")
        return True
      
      age = time.time() - self.download_timestamp
      logger.debug(f"Cache age: {age}s, TTL: {self.ttl}s, Expired: {age > self.ttl}")
      return age > self.ttl

  async def fetch_and_cache_image(self) -> bool:
      """Fetch a random image and cache it locally."""
      logger.debug("Fetching new image from external source")
      img_url = "https://picsum.photos/500"
      try:
          async with aiohttp.ClientSession() as session:
              async with session.get(img_url) as resp:
                  if resp.status == 200:
                      img_bytes = await resp.read()
                      with open(self.image_path, "wb") as f:
                          f.write(img_bytes)
                      self.download_timestamp = time.time()
                      # Reset grace period flag on new fetch
                      self.grace_period_used = False
                      self._save_metadata()
                      logger.debug(f"Image fetched and cached successfully at {self.download_timestamp}")
                      return True
      except Exception as e:
          logger.error(f"Failed to fetch image: {e}")
      return False


      
async def lifespan(app: FastAPI):
    """Fetch image on startup if cache is expired, initialize cache with metadata support."""
    global cache

    # Use explicit environment variable default inline
    cache_dir = os.getenv("CACHE_DIR", "./cache")
    cache = ImageCache(cache_dir=cache_dir)
    logger.debug(f"Lifespan startup: Cache initialized with dir {cache_dir}")
    
    if cache.is_cache_expired():
        logger.debug("Lifespan startup: Cache is expired on startup, fetching new image")
        fetched = await cache.fetch_and_cache_image()
        if fetched:
            logger.debug("Lifespan startup: Image fetched and cached successfully on startup")
        else:
            logger.error("Lifespan startup: Failed to fetch image on startup")
    else:
        logger.debug("Lifespan startup: Cache valid on startup, using existing image")
    yield  # Lifespan yield point; app runs here
    # TODO: shutdown logic here
    logger.debug("Lifespan shutdown: Application is shutting down")

# Cache global is optional but good to explicitly declare
cache: ImageCache | None = None  # type hint for clarity (Python 3.10+)

logger.debug(f"Setting up FastAPI app with lifespan")
app = FastAPI(lifespan=lifespan)
logger.debug(f"FastAPI app setup complete")

@app.get("/", response_class=HTMLResponse)
async def main_page():
  """Main page that serves the cached image with metadata info."""
  global cache
  if cache is None:
    raise HTTPException(status_code=500, detail="Cache not initialized")
  
  if cache.is_cache_expired():
    logger.debug("main_page endpoint: Cache expired")
    if not cache.grace_period_used and os.path.exists(cache.image_path):
      logger.debug("main_page endpoint: Serving cached image under grace period")
      cache.grace_period_used = True
      cache._save_metadata()  # Persist grace period change
    else:
      logger.debug("main_page endpoint: Fetching new image as grace period used or no cached image")
      success = await cache.fetch_and_cache_image()
      if not success:
          logger.error("main_page endpoint: Failed to fetch new image")
  else:
      logger.debug("main_page endpoint: Cache valid, serving cached image")
  
  cache.record_access()
  download_time = cache.download_timestamp
  expiry_time = download_time + cache.ttl if download_time else None
  last_access = cache.last_access_time
  access_count = cache.access_count
  image_access_count = cache.access_count
  grace_status = "Grace period" if cache.grace_period_used else ("Valid" if download_time and time.time() < expiry_time else "Expired")  

  html_content = f"""
    <html>
    <head><title>The Project App</title></head>
    <body>
    <h1>The Project App</h1>
    <hr/>
    <img src="/image" alt="Random Image"/>
    <hr/>
    <p>DevOps with Kubernetes 2025</p>
    <div style="position: fixed; bottom: 10px; right: 10px; font-size: 12px; color: #999; border: 1px solid #ccc; padding: 6px;">
      <b>Image Cache Metadata</b><br/>
      Image Download time: {time.ctime(download_time) if download_time else 'N/A'}<br/>
      Image Expiry time: {time.ctime(expiry_time) if expiry_time else 'N/A'}<br/>
      Site Access count: {access_count}<br/>
      Image Access count: {image_access_count}<br/>
      Last Site Access: {time.ctime(last_access) if last_access else 'N/A'}<br/>
      Status: {grace_status}<br/>
    </div>
    </body>
    </html>
    """
  return HTMLResponse(content=html_content)

@app.get("/image")
async def get_image():
  if cache is None or not os.path.exists(cache.image_path):
      raise HTTPException(status_code=404, detail="Image not available")
  return FileResponse(cache.image_path, media_type="image/jpeg")
  
