#!/usr/bin/env python3
"""Start the daily collection scheduler."""

import logging
import signal
import sys

from src.scheduler.daily_job import create_scheduler, DailyCollectionJob
from src.utils.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scheduler.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info("Shutting down scheduler...")
    sys.exit(0)


def run_once():
    """Run a single collection job (for testing)."""
    logger.info("Running single collection job...")
    job = DailyCollectionJob()
    result = job.run()
    logger.info(f"Job complete: {result}")


def run_scheduler():
    """Run the continuous scheduler."""
    config = get_config()
    schedule_config = config.settings.get("schedule", {})

    logger.info("Starting scheduler...")
    logger.info(f"Daily collection: {schedule_config.get('daily_collection', {}).get('hour', 9)}:00")

    scheduler = create_scheduler()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Knowledge Base Scheduler")
    parser.add_argument("--run-once", action="store_true", help="Run job once and exit")
    args = parser.parse_args()

    if args.run_once:
        run_once()
    else:
        run_scheduler()
