from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="ParlAi Backend",
    description="AI-Powered Betting Slip Analyzer",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "ParlAi Brain is active"}