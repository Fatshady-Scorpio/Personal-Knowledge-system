"""Web Search — Web search integration interface.

Web search is performed at the Agent level (Claude Code's built-in WebSearch tool),
not within Python code, because:
- DuckDuckGo/Google are blocked in China
- Claude Code's WebSearch tool works natively

This module provides the interface and result formatting.
Actual web search is triggered by the search CLI when run under Claude Code.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WebResult:
    """A single web search result."""
    title: str
    url: str
    snippet: str
    source: str = "web"
