"""Search Engine — Main orchestrator for wiki search.

Ties together: QueryRouter → IndexManager → LocalRetriever → Synthesizer
"""

import logging
from pathlib import Path
from typing import Optional

from .indexer import IndexManager
from .local_retriever import LocalRetriever
from .query_router import QueryRouter, QueryIntent
from .synthesizer import Synthesizer
from .web_search import WebResult, DuckDuckGoSearch
from ..domain_manager import DomainManager

logger = logging.getLogger(__name__)


class SearchEngine:
    """Personal wiki search engine.

    Pipeline:
    1. Route query → determine target domain(s)
    2. Retrieve entries → BM25 + link expansion
    3. Synthesize answer → LLM generates (wiki-only or wiki+web hybrid)
    """

    def __init__(
        self,
        wiki_root: Path,
        model: str = "qwen3.6-plus",
        domain: Optional[str] = None,
        use_web: bool = False,
    ):
        self.wiki_root = wiki_root
        self.domain = domain
        self.use_web = use_web
        self.domain_manager = DomainManager()
        self.index_manager = IndexManager(wiki_root)
        self.query_router = QueryRouter(self.domain_manager)
        self.synthesizer = Synthesizer(model=model)

        # DuckDuckGo fallback (works with VPN)
        self.ddg = DuckDuckGoSearch() if use_web else None

    def search(
        self,
        query: str,
        synthesize: bool = True,
        web_results: Optional[list[WebResult]] = None,
    ) -> dict:
        """Perform a wiki search.

        Args:
            query: User query
            synthesize: Whether to generate an LLM answer
            web_results: Optional web search results (injected by CLI/Agent)

        Returns:
            Dictionary with:
            - intent: QueryIntent (domain routing)
            - results: List of retrieved entries
            - answer: Synthesized answer (if synthesize=True)
            - entry_count: Number of wiki entries retrieved
        """
        # Step 1: Route query
        intent = self.query_router.route(query)
        if self.domain:
            intent.primary_domain = self.domain
        logger.info(
            f"Query routed to domain: {intent.primary_domain} "
            f"(confidence={intent.confidence:.2f})"
        )

        # Step 2: Retrieve from target domain
        domain_index = self.index_manager.get_index(intent.primary_domain)
        retriever = LocalRetriever(domain_index, self.wiki_root)
        results = retriever.retrieve(query, top_k=5)

        # Step 3: Optional multi-domain retrieval
        if intent.is_multi_domain:
            for secondary in intent.secondary_domains[:2]:
                sec_index = self.index_manager.get_index(secondary)
                sec_retriever = LocalRetriever(sec_index, self.wiki_root)
                sec_results = sec_retriever.retrieve(query, top_k=3)
                results.extend(sec_results)

        # Step 4: Synthesize answer (hybrid: wiki + web if needed)
        answer = ""
        if synthesize:
            # Auto-trigger web search if wiki is thin and web is enabled
            effective_web = web_results
            if not effective_web and self.use_web and self.ddg:
                bm25_count = sum(1 for r in results if r["source"] == "bm25")
                if bm25_count < 3:
                    logger.info("Auto-triggering DuckDuckGo (thin wiki results)")
                    effective_web = self.ddg.search(query)

            domain_name = self.domain_manager.get_domain(intent.primary_domain)
            answer = self.synthesizer.synthesize_hybrid(
                query=query,
                wiki_results=results,
                web_results=effective_web,
                domain_name=domain_name.name if domain_name else intent.primary_domain,
            )

        return {
            "intent": intent,
            "results": results,
            "answer": answer,
            "entry_count": len(results),
        }

    def retrieve_only(self, query: str, domain: Optional[str] = None) -> list[dict]:
        """Retrieve entries without synthesis (for inspection/debugging).

        Args:
            query: User query
            domain: Override domain

        Returns:
            List of {name, score, content, source}
        """
        target = domain or self.query_router.route(query).primary_domain
        domain_index = self.index_manager.get_index(target)
        retriever = LocalRetriever(domain_index, self.wiki_root)
        return retriever.retrieve(query, top_k=10)

    def build_indexes(self) -> dict[str, int]:
        """Rebuild all domain indexes.

        Returns:
            Dict of {domain: entry_count}
        """
        return self.index_manager.build_all()
