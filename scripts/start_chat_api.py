#!/usr/bin/env python3
"""Start the Agentic Wiki chat API server.

Usage:
    PYTHONPATH=. python scripts/start_chat_api.py [options]

Options:
    --host HOST     Host to bind (default: 127.0.0.1)
    --port PORT     Port to listen on (default: 8000)
    --reload        Enable auto-reload for development
"""

import argparse
import logging
import uvicorn
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Start Agentic Wiki chat API server")
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    args = parser.parse_args()

    # Get project root
    root_dir = Path(__file__).parent.parent

    logger.info(f"Starting Agentic Wiki API server on {args.host}:{args.port}")
    logger.info(f"API docs: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "src.server.wiki_chat_api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        app_dir=str(root_dir),
    )


if __name__ == "__main__":
    main()
