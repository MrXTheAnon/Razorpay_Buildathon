import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.core.database import init_db
from backend.app.api.v1.webhooks import router as webhooks_router
from backend.app.api.v1.recovery import router as recovery_router
from backend.app.api.v1.checkout import router as checkout_router
from backend.app.services.telegram_listener import telegram_listener

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("razorloop.main")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous Bounded AI Revenue Recovery Agent for Razorpay Buildathon (Track 03)"
)

# CORS middleware for local dev & frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(webhooks_router, prefix=settings.API_V1_STR)
app.include_router(recovery_router, prefix=settings.API_V1_STR)
app.include_router(checkout_router)

polling_task = None

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing RazorLoop database...")
    await init_db()
    
    logger.info("Starting Telegram long-polling listener...")
    global polling_task
    polling_task = asyncio.create_task(telegram_listener.start())

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Stopping Telegram listener...")
    telegram_listener.stop()
    global polling_task
    if polling_task and not polling_task.done():
        polling_task.cancel()
        try:
            await asyncio.wait_for(asyncio.shield(polling_task), timeout=0.5)
        except (asyncio.CancelledError, asyncio.TimeoutError, Exception):
            pass

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
async def root():
    index_file = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "track": "Track 03: AI Revenue Recovery",
        "docs": "/docs",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    return {"status": "ok", "telegram_polling": telegram_listener.is_running}

@app.get("/api/status")
async def api_status():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "track": "Track 03: AI Revenue Recovery",
        "docs": "/docs",
        "status": "healthy"
    }
