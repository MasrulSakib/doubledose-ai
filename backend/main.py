from fastapi import FastAPI

app = FastAPI(
    title="DoubleDose AI API",
    description="Medicine ingredient overlap checker",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "DoubleDose AI API",
    }