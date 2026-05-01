"""Web Search — Web search integration.

Primary: Claude Code Agent-level WebSearch tool (works behind GFW).
Fallback: DuckDuckGo HTTP (works with VPN).

This module provides the WebResult dataclass and an optional
DuckDuckGo HTTP client for VPN scenarios.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class WebResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    source: str = "web"


class DuckDuckGoSearch:
    """Optional DuckDuckGo HTTP search (works with VPN).

    Use this when running with VPN. Falls back gracefully
    when DuckDuckGo is unreachable.
    """

    def __init__(self, max_results: int = 5, timeout_s: int = 10):
        self.max_results = max_results
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        })

    def search(self, query: str) -> list[WebResult]:
        """Search DuckDuckGo HTML interface."""
        try:
            response = self.session.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                timeout=self.timeout_s,
            )
            response.raise_for_status()
            return self._parse(response.text)
        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {e}")
            return []

    def _parse(self, html: str) -> list[WebResult]:
        """Parse DuckDuckGo HTML response."""
        results = []
        blocks = re.findall(
            r'<div class="result[^"]*">(.*?)</div>\s*</div>',
            html, re.DOTALL,
        )
        for block in blocks:
            title_match = re.search(
                r'<a class="result__a" href="([^"]+)">(.*?)</a>',
                block, re.DOTALL,
            )
            if not title_match:
                continue

            url = title_match.group(1)
            title = re.sub(r'<[^>]+>', "", title_match.group(2)).strip()

            snippet_match = re.search(
                r'<a class="result__snippet[^"]*">(.*?)</a>',
                block, re.DOTALL,
            )
            snippet = ""
            if snippet_match:
                snippet = re.sub(r'<[^>]+>', "", snippet_match.group(1)).strip()

            if title:
                results.append(WebResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source="duckduckgo",
                ))

        return results[:self.max_results]
