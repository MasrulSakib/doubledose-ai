
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.medicines import router as medicines_router
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Medicine ingredient overlap checker",
)

app.include_router(health_router)
app.include_router(medicines_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to DoubleDose AI API",
        "docs": "/docs",
        "health": "/health",
    }
