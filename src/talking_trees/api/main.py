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
# Default to localhost for development. For production, set TALKINGTREES_CORS_ORIGINS environment variable
# Example: TALKINGTREES_CORS_ORIGINS="https://app.example.com,https://editor.example.com"
cors_origins_env = os.getenv("TALKINGTREES_CORS_ORIGINS", "")
if cors_origins_env:
    # Production: use specific origins from environment variable
    allowed_origins = [origin.strip() for origin in cors_origins_env.split(",")]
else:
    # Development: allow localhost and common dev ports
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:5173",  # Vite default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
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
