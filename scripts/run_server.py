#!/usr/bin/env python3
"""Run knowledge API server."""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Knowledge API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    uvicorn.run(
        "src.server.app:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True
    )


if __name__ == "__main__":
    main()
