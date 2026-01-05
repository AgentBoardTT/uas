"""Universal Agent SDK - Web Application API Server."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .container_manager import container_manager
from .models import HealthResponse
from .routes import agents_router, chat_router, configs_router, files_router
from .session_manager import session_manager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Universal Agent SDK API Server")
    session_manager.set_container_manager(container_manager)
    await session_manager.start()
    yield
    # Shutdown
    logger.info("Shutting down Universal Agent SDK API Server")
    await session_manager.stop()


app = FastAPI(
    title="Universal Agent SDK API",
    description="API server for Universal Agent SDK web application",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(chat_router)
app.include_router(configs_router)
app.include_router(files_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    sessions = await session_manager.list_sessions()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        active_sessions=len(sessions),
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Universal Agent SDK API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
