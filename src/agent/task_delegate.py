"""Task delegate for complex knowledge operations."""

from typing import Optional, Callable
from pathlib import Path
import json
from datetime import datetime

from ..collector import WebScraper, RSSFetcher
from ..processor.summarizer import Summarizer
from ..retriever.rag_qa import RAGQA
from ..utils.config import get_config


class TaskDelegate:
    """Handle complex delegated tasks using knowledge base capabilities."""

    def __init__(self, knowledge_root: str | Path | None = None):
        self.config = get_config()
        self.knowledge_root = Path(knowledge_root or self.config.paths.get("knowledge_root", "./knowledge"))

        self.scraper = WebScraper()
        self.fetcher = RSSFetcher()
        self.summarizer = Summarizer(output_dir=str(self.knowledge_root / "20-Processed"))

    def scrape_and_process(self, url: str, save: bool = True) -> dict:
        """Scrape URL and process content.

        Args:
            url: URL to scrape
            save: Whether to save to knowledge base

        Returns:
            Processing result with summary
        """
        # Scrape content
        scraped = self.scraper.scrape(url)

        # Generate summary
        summary = self.summarizer.summarize_text(scraped["content"])

        # Save if requested
        if save:
            filepath = self.summarizer.save_to_file(
                scraped["content"],
                title=scraped.get("title", "Scraped Content"),
                source_url=url
            )
        else:
            filepath = None

        return {
            "title": scraped.get("title"),
            "url": url,
            "summary": summary,
            "saved_to": filepath,
            "scraped_at": datetime.now().isoformat()
        }

    def fetch_rss_and_summarize(self, feed_url: str, limit: int = 5) -> list[dict]:
        """Fetch RSS feed and summarize entries.

        Args:
            feed_url: RSS feed URL
            limit: Number of entries to fetch

        Returns:
            List of processed entries
        """
        entries = self.fetcher.fetch(feed_url, limit=limit)
        results = []

        for entry in entries:
            summary = self.summarizer.summarize_text(entry.get("content", ""))
            results.append({
                "title": entry.get("title"),
                "url": entry.get("link"),
                "summary": summary,
                "published": entry.get("published"),
                "fetched_at": datetime.now().isoformat()
            })

        return results

    def research_topic(self, topic: str, depth: int = 2) -> dict:
        """Research a topic using knowledge base.

        Args:
            topic: Topic to research
            depth: How deep to search (1=basic, 2=with related, 3=deep dive)

        Returns:
            Research summary
        """
        # Import here to avoid circular imports
        from ..retriever.embedder import Embedder
        from ..retriever.vector_store import VectorStore

        embedder = Embedder(api_key=self.config.bailian_api_key)
        vector_store = VectorStore(
            dimension=1536,
            index_path=self.config.settings.get("retriever", {}).get("index_path")
        )
        rag_qa = RAGQA(
            embedder=embedder,
            vector_store=vector_store,
            model=self.config.settings.get("retriever", {}).get("rag", {}).get("model", "qwen3.5-plus")
        )

        # Get answer with context
        result = rag_qa.answer(topic, top_k=5 * depth)

        return {
            "topic": topic,
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "researched_at": datetime.now().isoformat()
        }

    def get_available_capabilities(self) -> list[str]:
        """List available capabilities.

        Returns:
            List of capability descriptions
        """
        return [
            "scrape_and_process: Scrape URL and generate summary",
            "fetch_rss_and_summarize: Fetch RSS feed and summarize entries",
            "research_topic: Research topic using knowledge base",
            "semantic_search: Search knowledge base by query",
            "rag_qa: Answer questions using RAG"
        ]
