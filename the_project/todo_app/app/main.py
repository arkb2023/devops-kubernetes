from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routes import frontend

app = FastAPI(lifespan=frontend.lifespan)

# Mount static directory to serve JS/CSS files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialize templates pointing to your templates directory
templates = Jinja2Templates(directory="app/templates")

# Include routers (you may pass templates as dependency or import inside routes)
app.include_router(frontend.router)
