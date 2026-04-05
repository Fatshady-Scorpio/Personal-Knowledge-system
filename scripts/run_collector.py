#!/usr/bin/env python3
"""Collector service runner."""

import asyncio
import argparse
from pathlib import Path

from src.collector import WebScraper, RSSFetcher
from src.processor.summarizer import Summarizer
from src.graph import GraphStore, LinkAnalyzer
from src.utils.config import get_config


async def scrape_url(url: str, output_dir: str):
    """Scrape a URL and process the content."""
    scraper = WebScraper()
    summarizer = Summarizer(output_dir=output_dir)

    print(f"Scraping: {url}")
    content = await scraper.scrape(url)

    markdown = summarizer.process_to_markdown(
        content["content"],
        title=content["title"],
        source_url=content["source_url"]
    )

    filepath = summarizer.save_to_file(
        content["content"],
        title=content["title"],
        source_url=content["source_url"]
    )

    print(f"Saved: {filepath}")
    await scraper.close()


async def fetch_rss(feed_url: str, output_dir: str, limit: int = 5):
    """Fetch RSS feed and process entries."""
    fetcher = RSSFetcher()
    summarizer = Summarizer(output_dir=output_dir)

    print(f"Fetching: {feed_url}")
    entries = await fetcher.fetch(feed_url, limit=limit)

    for entry in entries:
        filepath = summarizer.save_to_file(
            entry["content"],
            title=entry["title"],
            source_url=entry["source_url"]
        )
        print(f"Saved: {filepath}")

    await fetcher.close()


def main():
    parser = argparse.ArgumentParser(description="Content Collector")
    parser.add_argument("command", choices=["scrape", "rss"], help="Command to run")
    parser.add_argument("--url", required=True, help="URL or RSS feed URL")
    parser.add_argument("--limit", type=int, default=5, help="Limit for RSS entries")
    parser.add_argument("--output", help="Output directory")

    args = parser.parse_args()

    config = get_config()
    output_dir = args.output or Path(config.paths["knowledge_root"]) / "20-Processed"

    if args.command == "scrape":
        asyncio.run(scrape_url(args.url, str(output_dir)))
    elif args.command == "rss":
        asyncio.run(fetch_rss(args.url, str(output_dir), args.limit))


if __name__ == "__main__":
    main()
