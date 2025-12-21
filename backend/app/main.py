"""
FastAPI Main Application
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db
from app.protocols.telnet_server import TelnetServer
from app.api import admin, bbs

# Import models to ensure tables are created
from app.models.user import User
from app.models.board import Board, Message
from app.models.system_message import SystemMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Global telnet server instance
telnet_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting MTBBS Linux Server...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize default messages if not exists
    from app.services.message_service import MessageService
    message_service = MessageService()
    count = await message_service.initialize_default_messages()
    if count > 0:
        logger.info(f"Initialized {count} default system messages")

    # Start Telnet server
    global telnet_server
    telnet_server = TelnetServer(
        host=settings.TELNET_HOST,
        port=settings.TELNET_PORT
    )

    # Run Telnet server in background
    telnet_task = asyncio.create_task(telnet_server.start())
    logger.info(f"Telnet server starting on {settings.TELNET_HOST}:{settings.TELNET_PORT}")

    yield

    # Shutdown
    logger.info("Shutting down MTBBS Linux Server...")
    if telnet_server:
        await telnet_server.stop()

    telnet_task.cancel()
    try:
        await telnet_task
    except asyncio.CancelledError:
        pass

    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MTBBS Linux - Modern BBS System with Telnet & Web UI",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(bbs.router, prefix="/api/bbs", tags=["bbs"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "telnet": {
            "host": settings.TELNET_HOST,
            "port": settings.TELNET_PORT,
            "active_connections": telnet_server.get_active_connections() if telnet_server else 0,
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Mount static files for admin UI
# app.mount("/admin", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
