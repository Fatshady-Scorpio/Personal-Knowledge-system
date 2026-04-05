"""API routes for knowledge services."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from src.agent.knowledge_api import KnowledgeAPI
from src.agent.context_injector import ContextInjector
from src.agent.task_delegate import TaskDelegate


# Initialize services
knowledge_api = KnowledgeAPI()
context_injector = ContextInjector()
task_delegate = TaskDelegate()


# Search router
search_router = APIRouter()


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchResponse(BaseModel):
    results: list[dict]


@search_router.post("", response_model=SearchResponse)
def search(request: SearchRequest):
    """Search knowledge base."""
    results = knowledge_api.search(request.query, top_k=request.top_k)
    return SearchResponse(results=results)


@search_router.get("")
def search_get(query: str = Query(...), top_k: int = 5):
    """Search knowledge base (GET)."""
    results = knowledge_api.search(query, top_k=top_k)
    return {"results": results}


# Q&A router
qa_router = APIRouter()


class QARequest(BaseModel):
    question: str
    top_k: int = 5


class QAResponse(BaseModel):
    answer: str
    sources: list[dict]


@qa_router.post("", response_model=QAResponse)
def answer(request: QARequest):
    """Answer question using RAG."""
    result = knowledge_api.answer(request.question, top_k=request.top_k)
    return QAResponse(answer=result["answer"], sources=result.get("sources", []))


@qa_router.get("")
def answer_get(question: str = Query(...), top_k: int = 5):
    """Answer question (GET)."""
    result = knowledge_api.answer(question, top_k=top_k)
    return {"answer": result["answer"], "sources": result.get("sources", [])}


# Context router
context_router = APIRouter()


class ContextRequest(BaseModel):
    query: str
    max_notes: int = 5
    include_full_content: bool = False
    session_id: str = "default"


@context_router.post("/get")
def get_context(request: ContextRequest):
    """Get relevant context for query."""
    context = context_injector.get_context(
        request.query,
        max_notes=request.max_notes,
        include_full_content=request.include_full_content
    )
    return {"context": context}


@context_router.post("/save")
def save_context(request: ContextRequest):
    """Save context for session."""
    context = context_injector.get_context(request.query, max_notes=request.max_notes)
    path = context_injector.save_context(request.query, context, request.session_id)
    return {"path": path}


@context_router.get("/load")
def load_context(session_id: str = Query(default="default")):
    """Load context for session."""
    context = context_injector.load_context(session_id)
    if context is None:
        raise HTTPException(status_code=404, detail="No context found")
    return {"context": context}


# Delegate router
delegate_router = APIRouter()


class ScrapeRequest(BaseModel):
    url: str
    save: bool = True


class RSSRequest(BaseModel):
    feed_url: str
    limit: int = 5


class ResearchRequest(BaseModel):
    topic: str
    depth: int = 2


@delegate_router.post("/scrape")
def scrape(request: ScrapeRequest):
    """Scrape URL and process content."""
    result = task_delegate.scrape_and_process(request.url, save=request.save)
    return result


@delegate_router.post("/rss")
def fetch_rss(request: RSSRequest):
    """Fetch RSS feed and summarize."""
    results = task_delegate.fetch_rss_and_summarize(request.feed_url, limit=request.limit)
    return {"entries": results}


@delegate_router.post("/research")
def research(request: ResearchRequest):
    """Research a topic."""
    result = task_delegate.research_topic(request.topic, depth=request.depth)
    return result


@delegate_router.get("/capabilities")
def get_capabilities():
    """List available capabilities."""
    return {"capabilities": task_delegate.get_available_capabilities()}
