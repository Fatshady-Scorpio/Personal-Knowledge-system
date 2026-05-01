"""Query Router — Intent classification → domain routing.

Reuses DomainManager for keyword-based domain classification.
Supports single-domain and multi-domain queries.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from ..domain_manager import DomainManager

logger = logging.getLogger(__name__)


@dataclass
class QueryIntent:
    """Parsed query intent."""
    query: str
    primary_domain: str
    confidence: float  # 0.0-1.0, how confident we are about domain
    is_multi_domain: bool = False
    secondary_domains: list[str] = None

    def __post_init__(self):
        if self.secondary_domains is None:
            self.secondary_domains = []


class QueryRouter:
    """Route queries to appropriate wiki domains."""

    def __init__(self, domain_manager: Optional[DomainManager] = None):
        self.domain_manager = domain_manager or DomainManager()

    def route(self, query: str) -> QueryIntent:
        """Classify query and determine target domain(s).

        Args:
            query: User query string

        Returns:
            QueryIntent with domain routing info
        """
        domain_id = self.domain_manager.classify_text(query)
        enabled = self.domain_manager.list_domains()

        # Calculate confidence based on score gap
        scores = {}
        query_lower = query.lower()
        for d in enabled:
            score = sum(1 for kw in d.keywords if kw.lower() in query_lower)
            scores[d.id] = score

        # Normalize confidence
        max_score = max(scores.values()) if scores else 0
        total = sum(scores.values()) if scores else 1
        confidence = max_score / total if total > 0 else 0.0

        # Determine if multi-domain
        secondary = []
        if max_score > 0 and len(scores) > 1:
            for did, sc in sorted(scores.items(), key=lambda x: -x[1]):
                if did != domain_id and sc > 0:
                    secondary.append(did)

        return QueryIntent(
            query=query,
            primary_domain=domain_id,
            confidence=confidence,
            is_multi_domain=len(secondary) > 0,
            secondary_domains=secondary,
        )
