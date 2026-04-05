"""Tests for web scraper."""

import pytest
import asyncio
from src.collector.web_scraper import WebScraper


class TestWebScraper:
    """Test WebScraper class."""

    @pytest.mark.asyncio
    async def test_scrape_article(self):
        """Test scraping a sample article."""
        scraper = WebScraper()

        # Use a simple test page
        result = await scraper.scrape("https://httpbin.org/html")

        assert "title" in result
        assert "content" in result
        assert result["source_url"] == "https://httpbin.org/html"

        await scraper.close()
