"""RSS feed fetcher."""

import feedparser
import httpx
from typing import Optional
from datetime import datetime


class RSSFetcher:
    """Fetch articles from RSS feeds."""

    def __init__(self, timeout: int = 30):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; PersonalKB/1.0; RSS Fetcher)"
        }

    async def fetch(self, feed_url: str, limit: int = 10) -> list[dict]:
        """Fetch latest entries from RSS feed.

        Args:
            feed_url: The RSS feed URL
            limit: Maximum number of entries to fetch

        Returns:
            List of entry dictionaries
        """
        response = await self.client.get(feed_url, headers=self.headers)
        response.raise_for_status()

        feed = feedparser.parse(response.text)
        entries = []

        for entry in feed.entries[:limit]:
            entries.append({
                "title": entry.get("title", "Untitled"),
                "content": entry.get("summary", entry.get("description", "")),
                "source_url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "fetched_at": datetime.now().isoformat(),
                "feed_title": feed.feed.get("title", ""),
            })

        return entries

    async def close(self):
        await self.client.aclose()
