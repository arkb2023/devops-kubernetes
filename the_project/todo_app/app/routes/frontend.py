from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
import os
import time
import logging
from app.cache import ImageCache

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
backend_url = os.getenv("TODO_BACKEND_URL", "http://127.0.0.1:8000")
logger.info(f"frontend.py module loaded: LOG_LEVEL={LOG_LEVEL}, LOG_FORMAT={LOG_FORMAT}, BACKEND_URL={backend_url}")
logger.info(f"frontend.py: backend_url set to {backend_url}")
async def lifespan(app: FastAPI):
    """Fetch image on startup if cache is expired, initialize cache with metadata support."""
    global cache

    # Use explicit environment variable default inline
    cache_dir = os.getenv("CACHE_DIR", "./cache")
    cache = ImageCache(cache_dir=cache_dir)
    logger.info(f"Lifespan startup: Cache initialized with dir {cache_dir}")
    
    if cache.is_cache_expired():
        logger.info("Lifespan startup: Cache is expired on startup, fetching new image")
        fetched = await cache.fetch_and_cache_image()
        if fetched:
            logger.info("Lifespan startup: Image fetched and cached successfully on startup")
        else:
            logger.error("Lifespan startup: Failed to fetch image on startup")
    else:
        logger.info("Lifespan startup: Cache valid on startup, using existing image")
    yield  # Lifespan yield point; app runs here
    # TODO: shutdown logic here
    logger.info("Lifespan shutdown: Application is shutting down")

# Cache global is optional but good to explicitly declare
cache: ImageCache | None = None  # type hint for clarity (Python 3.10+)

@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
  """Main page that serves the cached image with metadata info."""
  global cache
  if cache is None:
    raise HTTPException(status_code=500, detail="Cache not initialized")
  
  if cache.is_cache_expired():
    logger.info("main_page endpoint: Cache expired")
    if not cache.grace_period_used and os.path.exists(cache.image_path):
      logger.info("main_page endpoint: Serving cached image under grace period")
      cache.grace_period_used = True
      cache._save_metadata()  # Persist grace period change
    else:
      logger.info("main_page endpoint: Fetching new image as grace period used or no cached image")
      success = await cache.fetch_and_cache_image()
      if not success:
          logger.error("main_page endpoint: Failed to fetch new image")
  else:
      logger.info("main_page endpoint: Cache valid, serving cached image")
  
  cache.record_access()
  
  download_time_str = time.ctime(cache.download_timestamp) if cache.download_timestamp else 'N/A'
  expiry_time_str = time.ctime(cache.download_timestamp + cache.ttl) if cache.download_timestamp else 'N/A'
  last_access_str = time.ctime(cache.last_access_time) if cache.last_access_time else 'N/A'
  grace_status = "Grace period" if cache.grace_period_used else ("Valid" if cache.download_timestamp and time.time() < cache.download_timestamp + cache.ttl else "Expired")
  return templates.TemplateResponse("index.html", {
        # Request contains the ASGI scope and is mandatory 
        # for Jinja2 templating in FastAPI to 
        # generate correct URLs and for internal handling.
        "request": request,
        "download_time": download_time_str,
        "expiry_time": expiry_time_str,
        "access_count": cache.access_count,
        "image_access_count": cache.image_access_count,
        "last_access": last_access_str,
        "grace_status": grace_status,
        "backend_url": backend_url,
    })

@router.get("/image")
async def get_image():
  if cache is None or not os.path.exists(cache.image_path):
      raise HTTPException(status_code=404, detail="Image not available")
  return FileResponse(cache.image_path, media_type="image/jpeg")
  
