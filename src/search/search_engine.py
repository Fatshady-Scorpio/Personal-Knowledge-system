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
from ..domain_manager import DomainManager

logger = logging.getLogger(__name__)


class SearchEngine:
    """Personal wiki search engine.

    Pipeline:
    1. Route query → determine target domain(s)
    2. Retrieve entries → BM25 + link expansion
    3. Synthesize answer → LLM generates response
    """

    def __init__(
        self,
        wiki_root: Path,
        model: str = "qwen3.6-plus",
        domain: Optional[str] = None,
    ):
        self.wiki_root = wiki_root
        self.domain = domain
        self.domain_manager = DomainManager()
        self.index_manager = IndexManager(wiki_root)
        self.query_router = QueryRouter(self.domain_manager)
        self.synthesizer = Synthesizer(model=model)

    def search(self, query: str, synthesize: bool = True) -> dict:
        """Perform a wiki search.

        Args:
            query: User query
            synthesize: Whether to generate an LLM answer

        Returns:
            Dictionary with:
            - intent: QueryIntent (domain routing)
            - results: List of retrieved entries
            - answer: Synthesized answer (if synthesize=True)
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

        # Step 4: Synthesize answer
        answer = ""
        if synthesize and results:
            domain_name = self.domain_manager.get_domain(intent.primary_domain)
            answer = self.synthesizer.synthesize_local(
                query=query,
                results=results,
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
