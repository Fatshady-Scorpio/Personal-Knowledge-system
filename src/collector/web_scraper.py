"""Web scraper for collecting articles."""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime


class WebScraper:
    """Scrape articles from websites."""

    def __init__(self, timeout: int = 30):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; PersonalKB/1.0)"
        }

    async def scrape(self, url: str) -> dict:
        """Scrape content from URL.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary with title, content, source_url, scraped_at
        """
        response = await self.client.get(url, headers=self.headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = soup.find("title")
        title_text = title.string.strip() if title else "Untitled"

        # Extract main content (simplified - can be enhanced)
        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text().strip() for p in paragraphs])

        return {
            "title": title_text,
            "content": content[:50000],  # Limit content length
            "source_url": url,
            "scraped_at": datetime.now().isoformat(),
        }

    async def close(self):
        await self.client.aclose()
