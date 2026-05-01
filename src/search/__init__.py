"""Search module — BM25-based wiki search engine.

Provides fast, domain-scoped retrieval with bilateral link expansion.
"""

from .indexer import IndexManager, DomainIndex, tokenize
from .local_retriever import LocalRetriever
from .query_router import QueryRouter, QueryIntent
from .search_engine import SearchEngine
from .synthesizer import Synthesizer
from .knowledge_weaver import KnowledgeWeaver, KnowledgeValue, WeaverResult

__all__ = [
    "IndexManager",
    "DomainIndex",
    "LocalRetriever",
    "QueryRouter",
    "QueryIntent",
    "SearchEngine",
    "Synthesizer",
    "KnowledgeWeaver",
    "KnowledgeValue",
    "WeaverResult",
    "WebResult",
    "DuckDuckGoSearch",
    "tokenize",
]
