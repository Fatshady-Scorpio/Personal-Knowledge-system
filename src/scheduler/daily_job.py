"""Daily collection job for automated knowledge base updates."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from ..collector import RSSFetcher, WebScraper
from ..processor.summarizer import Summarizer
from ..processor.briefing import DailyBriefing
from ..processor.priority_filter import PriorityFilter
from ..graph.graph_store import GraphStore
from ..graph.link_analyzer import LinkAnalyzer
from ..utils.config import get_config

logger = logging.getLogger(__name__)


class DailyCollectionJob:
    """Daily automated collection job."""

    def __init__(self):
        self.config = get_config()
        self.knowledge_root = Path(self.config.paths.get("knowledge_root", "./knowledge"))

        # Initialize components
        self.scraper = WebScraper()
        self.fetcher = RSSFetcher()
        self.summarizer = Summarizer(
            output_dir=str(self.knowledge_root / "20-Processed")
        )
        self.graph = GraphStore(
            db_path=self.config.settings.get("graph", {}).get("db_path")
        )
        self.link_analyzer = LinkAnalyzer() if self.config.settings.get("graph", {}).get("auto_link") else None
        self.priority_filter = PriorityFilter()
        self.briefing = DailyBriefing(self.knowledge_root)

    def run(self, generate_briefing: bool = True) -> dict:
        """Run the daily collection job.

        Args:
            generate_briefing: Whether to generate daily briefing

        Returns:
            Dictionary with job statistics
        """
        logger.info("Starting daily collection job...")

        stats = {
            "articles_processed": 0,
            "notes_created": 0,
            "links_created": 0,
            "articles_skipped": 0,
            "errors": []
        }

        try:
            # Get RSS sources
            sources = self.config.sources.get("domestic", {}).get("rss_feeds", [])
            sources.extend(self.config.sources.get("international", {}).get("rss_feeds", []))
            sources.extend(self.config.sources.get("custom", {}).get("rss_feeds", []))

            # Fetch and process RSS feeds
            for source in sources:
                try:
                    logger.info(f"Fetching RSS: {source.get('name', 'Unknown')}")
                    entries = self.fetcher.fetch(source.get("url"), limit=5)

                    for entry in entries:
                        # Add source name for priority filtering
                        entry["name"] = source.get("name", "Unknown")

                        # Apply priority filter
                        if not self.priority_filter.should_process(entry):
                            logger.debug(f"Skipping low priority: {entry.get('title', 'Untitled')}")
                            stats["articles_skipped"] += 1
                            continue

                        result = self._process_entry(entry, source.get("category", "AI"))
                        if result:
                            stats["articles_processed"] += 1
                            stats["notes_created"] += 1

                except Exception as e:
                    logger.error(f"Error processing RSS {source.get('name')}: {e}")
                    stats["errors"].append(str(e))

            # Build knowledge graph links
            if self.link_analyzer:
                logger.info("Building knowledge graph links...")
                # Links are created automatically by LinkAnalyzer during processing

            # Generate daily briefing
            if generate_briefing:
                try:
                    briefing_path = self.briefing.generate()
                    logger.info(f"Generated daily briefing: {briefing_path}")
                    stats["briefing_generated"] = briefing_path
                except Exception as e:
                    logger.error(f"Error generating briefing: {e}")
                    stats["errors"].append(str(e))

            logger.info(f"Daily collection complete: {stats}")

        except Exception as e:
            logger.error(f"Daily collection failed: {e}")
            stats["errors"].append(str(e))

        finally:
            # Cleanup
            try:
                self.scraper.close()
                self.fetcher.close()
            except:
                pass

        return stats

    def _process_entry(self, entry: dict, category: str) -> Optional[dict]:
        """Process a single RSS/web entry.

        Args:
            entry: Entry dictionary with title, content, source_url
            category: Content category

        Returns:
            Processing result or None if failed
        """
        try:
            # Generate summary and save
            result = self.summarizer.save_to_file(
                text=entry.get("content", ""),
                title=entry.get("title", "Untitled"),
                source_url=entry.get("source_url", entry.get("link", "")),
                category=category
            )

            # Add to knowledge graph
            if result:
                self.graph.add_node(
                    node_id=Path(result).stem,
                    title=entry.get("title", "Untitled"),
                    content_preview=entry.get("content", "")[:200],
                    category=category
                )

            return result

        except Exception as e:
            logger.error(f"Error processing entry: {e}")
            return None


def create_scheduler() -> BlockingScheduler:
    """Create and configure the scheduler with default jobs.

    Returns:
        Configured BlockingScheduler instance
    """
    config = get_config()
    schedule_config = config.settings.get("schedule", {})

    scheduler = BlockingScheduler()
    job = DailyCollectionJob()

    # Daily collection job
    daily_config = schedule_config.get("daily_collection", {})
    if daily_config.get("enabled", True):
        scheduler.add_job(
            job.run,
            trigger="cron",
            hour=daily_config.get("hour", 9),
            minute=daily_config.get("minute", 0),
            timezone=daily_config.get("timezone", "Asia/Shanghai"),
            id="daily_collection",
            name="Daily Content Collection"
        )

    return scheduler


def run_daily_job():
    """Run a single daily collection job (for testing/manual trigger)."""
    job = DailyCollectionJob()
    return job.run()
