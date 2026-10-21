
from fastapi import FastAPI
from app.api.ai import router as ai_router
from app.api.health import router as health_router
from app.api.medicines import router as medicines_router
from app.core.config import settings
from app.api.ocr import router as ocr_router
from app.api.matcher import router as matcher_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Medicine ingredient overlap checker",
)

app.include_router(health_router)
app.include_router(medicines_router)
app.include_router(ai_router, prefix="/api/v1")
app.include_router(ocr_router, prefix="/api/v1")
app.include_router(matcher_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Welcome to DoubleDose AI API",
        "docs": "/docs",
        "health": "/health",
    }
