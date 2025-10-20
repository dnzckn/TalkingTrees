#!/usr/bin/env python3
"""Run the PyForest API server.

This script starts the FastAPI development server.

Usage:
    python run_server.py [--host HOST] [--port PORT]
"""

import argparse
import sys

try:
    import uvicorn
except ImportError:
    print("Error: uvicorn is not installed!")
    print("Install it with: pip install uvicorn[standard]")
    sys.exit(1)


def main():
    """Run the server."""
    parser = argparse.ArgumentParser(description="Run PyForest API server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=True,
        help="Enable auto-reload (default: True)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  PyForest API Server")
    print("=" * 60)
    print(f"\nStarting server on http://{args.host}:{args.port}")
    print(f"API docs: http://{args.host}:{args.port}/docs")
    print(f"ReDoc: http://{args.host}:{args.port}/redoc")
    print("\nPress Ctrl+C to stop\n")

    uvicorn.run(
        "py_forest.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
