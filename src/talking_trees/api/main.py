"""FastAPI application for TalkingTrees."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from talking_trees.api.routers import (
    behaviors,
    debug,
    executions,
    history,
    profiling,
    trees,
    validation,
    visualization,
    websocket,
)

# Create FastAPI app
app = FastAPI(
    title="TalkingTrees API",
    description="REST API for TalkingTrees - Behavior Tree Management and Execution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for web editor support
# Default to allow all origins for development. For deployment, set TALKINGTREES_CORS_ORIGINS environment variable
# Example: TALKINGTREES_CORS_ORIGINS="https://app.example.com,https://editor.example.com"
cors_origins_env = os.getenv("TALKINGTREES_CORS_ORIGINS", "")
if cors_origins_env:
    # Deployment: use specific origins from environment variable
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",")]
    allow_all = False
else:
    # Development: allow all origins (including file:// URLs)
    allowed_origins = ["*"]
    allow_all = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=not allow_all,  # Can't use credentials with allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trees.router)
app.include_router(behaviors.router)
app.include_router(executions.router)
app.include_router(history.router)
app.include_router(websocket.router)
app.include_router(debug.router)
app.include_router(visualization.router)
app.include_router(validation.router)
app.include_router(profiling.router)


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "TalkingTrees API",
        "version": "1.0.0",
        "description": "Behavior Tree Management and Execution API",
        "endpoints": {
            "trees": "/trees - Tree library management",
            "behaviors": "/behaviors - Behavior schema for editors",
            "executions": "/executions - Execution control",
            "docs": "/docs - Interactive API documentation",
        },
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "talkingtrees-api"}
