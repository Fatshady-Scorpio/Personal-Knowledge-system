"""FastAPI server for Agentic Wiki chat API.

This provides HTTP endpoints for:
- Chat queries
- Knowledge base stats
- Q&A history

Usage:
    PYTHONPATH=. uvicorn src.server.wiki_chat_api:app --host 0.0.0.0 --port 8000
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..query.agent_query import AgentQuery
from ..maintenance.health_checker import HealthChecker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Wiki API",
    description="API for querying wiki knowledge base with LLM-powered agent",
    version="1.0.0",
)

# Enable CORS for Obsidian plugin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Project paths
ROOT_DIR = Path(__file__).parent.parent.parent
WIKI_DIR = ROOT_DIR / "wiki"
OUTPUTS_DIR = ROOT_DIR / "outputs" / "qa"


# Request/Response models
class ChatRequest(BaseModel):
    question: str
    save_result: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    has_more: bool = False


class StatsResponse(BaseModel):
    concepts: int
    topics: int
    qa_count: int
    index_exists: bool


class HealthResponse(BaseModel):
    status: str
    broken_links: int
    orphaned_entries: int
    report: Optional[str] = None


# Global agent instance (lazy initialized)
_agent: Optional[AgentQuery] = None
_health_checker: Optional[HealthChecker] = None


def get_agent() -> AgentQuery:
    """Get or create AgentQuery instance."""
    global _agent
    if _agent is None:
        _agent = AgentQuery(
            wiki_dir=WIKI_DIR,
            outputs_dir=OUTPUTS_DIR,
        )
    return _agent


def get_health_checker() -> HealthChecker:
    """Get or create HealthChecker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(wiki_dir=WIKI_DIR)
    return _health_checker


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Agentic Wiki API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /api/chat",
            "stats": "GET /api/stats",
            "health": "GET /api/health",
        },
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat with the wiki knowledge base.

    Args:
        request: Chat request with question

    Returns:
        Chat response with answer and sources
    """
    try:
        agent = get_agent()
        answer = agent.query(request.question, save_result=request.save_result)

        # Extract source links from answer ([[link]] format)
        import re
        sources = re.findall(r"\[\[([^\]]+)\]\]", answer)

        return ChatResponse(
            answer=answer,
            sources=sources,
            has_more=len(sources) > 0,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=StatsResponse)
async def stats():
    """Get knowledge base statistics."""
    concepts = list(WIKI_DIR.glob("concepts/*.md")) if WIKI_DIR.exists() else []
    topics = list(WIKI_DIR.glob("topics/*.md")) if WIKI_DIR.exists() else []
    qa_files = list(OUTPUTS_DIR.glob("*.md")) if OUTPUTS_DIR.exists() else []
    index_exists = (WIKI_DIR / "index.md").exists()

    return StatsResponse(
        concepts=len(concepts),
        topics=len(topics),
        qa_count=len(qa_files),
        index_exists=index_exists,
    )


@app.get("/api/health", response_model=HealthResponse)
async def health():
    """Run health check on knowledge base."""
    try:
        checker = get_health_checker()
        results = checker.run_full_check()

        return HealthResponse(
            status="healthy" if not results["broken_links"] else "warnings",
            broken_links=len(results["broken_links"]),
            orphaned_entries=len(results["orphaned_entries"]),
            report=checker.generate_report(results)[:1000],  # Truncate report
        )
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/qa/{question_prefix}")
async def list_qa(question_prefix: str, limit: int = 10):
    """List Q&A records matching a prefix.

    Args:
        question_prefix: Prefix to search in questions
        limit: Maximum number of results

    Returns:
        List of Q&A summaries
    """
    if not OUTPUTS_DIR.exists():
        return []

    results = []
    for qa_file in OUTPUTS_DIR.glob("*.md"):
        try:
            content = qa_file.read_text(encoding="utf-8")

            # Extract question from filename or frontmatter
            if question_prefix.lower() in qa_file.stem.lower():
                metadata = {}
                parts = content.split("---", 3)
                if len(parts) >= 3:
                    for line in parts[1].strip().split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()

                results.append({
                    "file": qa_file.name,
                    "question": metadata.get("question", qa_file.stem),
                    "answered_at": metadata.get("answered_at", ""),
                })

                if len(results) >= limit:
                    break

        except Exception as e:
            logger.warning(f"Failed to read Q&A file {qa_file}: {e}")

    return results


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
