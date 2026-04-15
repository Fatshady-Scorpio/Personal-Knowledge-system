"""Deep Query Engine for Agentic Wiki.

This module handles stateful queries over the wiki knowledge base.
"""

from .agent_query import AgentQuery
from .context_manager import ContextManager

__all__ = [
    "AgentQuery",
    "ContextManager",
]
