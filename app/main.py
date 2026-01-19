from fastapi import FastAPI
from contextlib import asynccontextmanager
import asyncio
from app.api.routes import router
from app.services.nfl_service import preload_nfl_data
from app.services.sgo_client import fetch_all_players_once

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Downloading NFL/NBA datasets...")
    
    # 1. Run blocking NFL download in a thread
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, preload_nfl_data)
    
    # 2. Prefetch SGO NBA Players
    # Create a dummy client just to fill the cache
    import httpx
    async with httpx.AsyncClient() as client:
        await fetch_all_players_once(client, "NBA")
    
    print("READY: System is hot and cached!")
    yield
    print("Shutting down...")

app = FastAPI(title="ParlAi Engine", version="1.0.0", lifespan=lifespan)

app.include_router(router, prefix="/api/v1")

@app.get("/")
def health_check():
    return {"status": "Active"}