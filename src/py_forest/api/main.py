"""FastAPI application for PyForest."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from py_forest.api.routers import (
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
    title="PyForest API",
    description="REST API for PyForest - Behavior Tree Management and Execution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for web editor support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
        "name": "PyForest API",
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
    return {"status": "healthy", "service": "pyforest-api"}
