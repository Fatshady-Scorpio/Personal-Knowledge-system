"""Phase 2 integration tests."""

import pytest
import asyncio
from pathlib import Path

from src.collector import WebScraper, RSSFetcher
from src.graph import GraphStore, LinkAnalyzer


class TestPhase2:
    """Test Phase 2 functionality."""

    @pytest.mark.asyncio
    async def test_scrape_and_process(self):
        """Test scraping and processing a URL."""
        scraper = WebScraper()
        result = await scraper.scrape("https://httpbin.org/html")

        assert "title" in result
        assert "content" in result
        await scraper.close()

    @pytest.mark.asyncio
    async def test_rss_fetch(self):
        """Test RSS fetching."""
        fetcher = RSSFetcher()
        # Use a valid RSS feed for testing
        entries = await fetcher.fetch("https://feeds2.feedburner.com/36kr", limit=3)

        assert isinstance(entries, list)
        await fetcher.close()

    def test_graph_operations(self, tmp_path):
        """Test graph store operations."""
        db_path = tmp_path / "test_graph.db"
        store = GraphStore(db_path)

        store.add_node("note1", "Test Note 1", tags=["test"])
        store.add_node("note2", "Test Note 2", tags=["test"])
        store.add_edge("note1", "note2", "related")

        related = store.get_related("note1")
        assert len(related) == 1
