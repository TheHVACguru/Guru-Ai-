"""
FastAPI application for Voice Assistant API.
"""

import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn

from assistant.api.auth import verify_token
from assistant.api.routes import create_router
from assistant.utils.logger import setup_logger

logger = setup_logger(__name__)

def create_app(config) -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Voice Assistant API",
        description="Open Source Voice-Activated Natural Language UI",
        version="1.0.0",
        docs_url="/docs" if config.debug_mode else None,
        redoc_url="/redoc" if config.debug_mode else None
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security
    security = HTTPBearer(auto_error=False)
    
    # Mount static files if web UI is enabled
    if config.enable_web_ui:
        web_dir = Path(__file__).parent.parent.parent / "web"
        if web_dir.exists():
            app.mount("/static", StaticFiles(directory=str(web_dir / "static")), name="static")
            
            @app.get("/", response_class=HTMLResponse)
            async def serve_web_ui():
                """Serve the web UI."""
                index_path = web_dir / "index.html"
                if index_path.exists():
                    return HTMLResponse(content=index_path.read_text(), status_code=200)
                else:
                    return HTMLResponse(content="<h1>Voice Assistant</h1><p>Web UI not found</p>", status_code=404)
    
    # Health check endpoint (no auth required)
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "voice-assistant-api",
            "version": "1.0.0"
        }
    
    # Include API routes with authentication
    api_router = create_router(config)
    app.include_router(api_router, prefix="/api/v1", dependencies=[Depends(verify_token)])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}")
        return HTTPException(status_code=500, detail="Internal server error")
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Startup event handler."""
        logger.info("Voice Assistant API starting up...")
        logger.info(f"API server running on {config.api_host}:{config.api_port}")
        if config.enable_web_ui:
            logger.info(f"Web UI available at http://{config.api_host}:{config.api_port}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Shutdown event handler."""
        logger.info("Voice Assistant API shutting down...")
    
    return app

async def run_api_server(config):
    """Run the API server."""
    app = create_app(config)
    
    uvicorn_config = uvicorn.Config(
        app,
        host=config.api_host,
        port=config.api_port,
        log_level="info" if not config.debug_mode else "debug",
        reload=config.debug_mode,
        access_log=config.debug_mode
    )
    
    server = uvicorn.Server(uvicorn_config)
    await server.serve()
