# Personal Knowledge Base Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现与 Claude/Agent 的深度集成，将知识库作为"长期记忆"，支持复杂任务委托和知识共享

**Architecture:** 在 Phase 3 基础上，增加 Agent 集成层，提供知识 API 和上下文注入能力

**Tech Stack:** 
- API 服务：FastAPI
- 上下文管理：SQLite + JSON
- Agent 通信：HTTP/REST API
- 任务队列：Celery (可选，用于异步任务)

---

## File Structure

### Files to Create

| File | Responsibility |
|------|----------------|
| `src/agent/__init__.py` | Agent 包初始化 |
| `src/agent/knowledge_api.py` | 知识库 API 服务 |
| `src/agent/context_injector.py` | 上下文注入器 |
| `src/agent/task_delegate.py` | 任务委托模块 |
| `src/agent/memory_store.py` | 长期记忆存储 |
| `src/server/__init__.py` | Server 包初始化 |
| `src/server/app.py` | FastAPI 应用 |
| `src/server/routes.py` | API 路由 |
| `scripts/run_server.py` | 服务启动脚本 |
| `scripts/claude_context.py` | Claude 上下文加载脚本 |
| `tests/test_knowledge_api.py` | API 测试 |
| `tests/test_context_injector.py` | 上下文测试 |

### Files to Modify

| File | Changes |
|------|---------|
| `requirements.txt` | 添加 FastAPI, uvicorn, pydantic |
| `config/settings.yaml` | 添加 Agent 集成配置 |
| `src/retriever/rag_qa.py` | 增强 RAG 支持多轮对话 |
| `README.md` | 更新 Phase 4 功能说明 |

---

## Module 1: Knowledge API (知识 API)

### Task 1.1: API 服务基础

**Files:**
- Create: `src/agent/__init__.py`
- Create: `src/agent/knowledge_api.py`

- [ ] **Step 1: 创建包初始化**

```python
"""Agent integration module."""

from .knowledge_api import KnowledgeAPI
from .context_injector import ContextInjector
from .task_delegate import TaskDelegate

__all__ = ["KnowledgeAPI", "ContextInjector", "TaskDelegate"]
```

- [ ] **Step 2: 创建 KnowledgeAPI 类**

```python
"""Knowledge API for external agent integration."""

from pathlib import Path
from typing import Optional
import json

from ..retriever.embedder import Embedder
from ..retriever.vector_store import VectorStore
from ..retriever.semantic_search import SemanticSearch
from ..retriever.rag_qa import RAGQA
from ..utils.config import get_config


class KnowledgeAPI:
    """External API for knowledge base access."""

    def __init__(self, knowledge_root: str | Path | None = None):
        self.config = get_config()
        self.knowledge_root = Path(knowledge_root or self.config.paths.get("knowledge_root", "./knowledge"))
        
        # Initialize retriever components
        self.embedder = Embedder(api_key=self.config.bailian_api_key)
        self.vector_store = VectorStore(
            dimension=1536,
            index_path=self.config.settings.get("retriever", {}).get("index_path")
        )
        self.semantic_search = SemanticSearch(
            embedder=self.embedder,
            vector_store=self.vector_store,
            knowledge_root=self.knowledge_root
        )
        self.rag_qa = RAGQA(
            embedder=self.embedder,
            vector_store=self.vector_store,
            model=self.config.settings.get("retriever", {}).get("rag", {}).get("model", "qwen3.5-plus")
        )

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Search knowledge base.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching documents
        """
        return self.semantic_search.search(query, top_k=top_k)

    def answer(self, question: str, top_k: int = 5) -> dict:
        """Answer question using knowledge base.

        Args:
            question: The question
            top_k: Number of context documents

        Returns:
            Dictionary with answer and sources
        """
        return self.rag_qa.answer(question, top_k=top_k)

    def get_note(self, title: str) -> dict | None:
        """Get a specific note by title.

        Args:
            title: Note title

        Returns:
            Note content and metadata
        """
        # Search in 20-Processed and 30-Topics
        for category in ["20-Processed", "30-Topics"]:
            note_path = self.knowledge_root / category / f"{title}.md"
            if note_path.exists():
                content = note_path.read_text(encoding="utf-8")
                return {
                    "title": title,
                    "content": content,
                    "path": str(note_path),
                    "category": category
                }
        return None

    def list_topics(self) -> list[str]:
        """List all topic categories.

        Returns:
            List of topic names
        """
        topics_dir = self.knowledge_root / "30-Topics"
        if not topics_dir.exists():
            return []
        return [d.name for d in topics_dir.iterdir() if d.is_dir()]

    def get_topic_notes(self, topic: str) -> list[dict]:
        """Get all notes in a topic.

        Args:
            topic: Topic name

        Returns:
            List of note metadata
        """
        topic_dir = self.knowledge_root / "30-Topics" / topic
        if not topic_dir.exists():
            return []

        notes = []
        for md_file in topic_dir.rglob("*.md"):
            notes.append({
                "title": md_file.stem,
                "path": str(md_file),
                "preview": md_file.read_text(encoding="utf-8")[:200]
            })
        return notes
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(agent): add KnowledgeAPI class

- Search knowledge base via API
- Answer questions using RAG
- Get notes by title
- List topics and topic notes
"
```

---

### Task 1.2: API 测试

**Files:**
- Create: `tests/test_knowledge_api.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for knowledge API."""

import pytest
from src.agent.knowledge_api import KnowledgeAPI
from src.utils.config import get_config


class TestKnowledgeAPI:
    """Test KnowledgeAPI class."""

    @pytest.fixture
    def api(self):
        """Create KnowledgeAPI instance."""
        return KnowledgeAPI()

    def test_search(self, api):
        """Test semantic search."""
        results = api.search("人工智能", top_k=3)
        assert isinstance(results, list)

    def test_answer(self, api):
        """Test RAG question answering."""
        result = api.answer("什么是机器学习？")
        assert "answer" in result

    def test_list_topics(self, api):
        """Test listing topics."""
        topics = api.list_topics()
        assert isinstance(topics, list)

    def test_get_note(self, api):
        """Test getting note by title."""
        # This may return None if no note exists yet
        note = api.get_note("Test")
        # Just verify it doesn't crash
        assert note is None or isinstance(note, dict)
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "test(agent): add KnowledgeAPI tests
"
```

---

## Module 2: Context Injector (上下文注入)

### Task 2.1: 上下文注入器

**Files:**
- Create: `src/agent/context_injector.py`

- [ ] **Step 1: 创建 ContextInjector 类**

```python
"""Context injector for Claude/Agent integration."""

from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from ..retriever.embedder import Embedder
from ..retriever.vector_store import VectorStore
from ..retriever.semantic_search import SemanticSearch
from ..utils.config import get_config


class ContextInjector:
    """Inject relevant knowledge context into Claude/Agent sessions."""

    def __init__(self, knowledge_root: str | Path | None = None):
        self.config = get_config()
        self.knowledge_root = Path(knowledge_root or self.config.paths.get("knowledge_root", "./knowledge"))
        self.context_dir = self.knowledge_root / ".claude_contexts"
        self.context_dir.mkdir(parents=True, exist_ok=True)

        # Initialize search
        self.embedder = Embedder(api_key=self.config.bailian_api_key)
        self.vector_store = VectorStore(
            dimension=1536,
            index_path=self.config.settings.get("retriever", {}).get("index_path")
        )
        self.semantic_search = SemanticSearch(
            embedder=self.embedder,
            vector_store=self.vector_store,
            knowledge_root=self.knowledge_root
        )

    def get_context(
        self,
        query: str,
        max_notes: int = 5,
        include_full_content: bool = False
    ) -> str:
        """Get relevant context as markdown-formatted string.

        Args:
            query: The topic or question to get context for
            max_notes: Maximum number of notes to include
            include_full_content: Whether to include full content or just preview

        Returns:
            Formatted context string
        """
        # Search for relevant notes
        results = self.semantic_search.search(query, top_k=max_notes, min_score=0.3)

        if not results:
            return "未找到相关的知识内容。"

        # Build context string
        context_parts = [f"# 相关知识上下文 (查询：{query})\n"]

        for i, r in enumerate(results, 1):
            context_parts.append(f"\n## {i}. {r['title']}\n")
            context_parts.append(f"**分类**: {r.get('category', 'Unknown')}\n")
            context_parts.append(f"**标签**: {', '.join(r.get('tags', []))}\n")
            context_parts.append(f"**来源**: {r.get('file_path', '')}\n\n")

            if include_full_content and r.get('file_path'):
                try:
                    content = Path(r['file_path']).read_text(encoding='utf-8')
                    context_parts.append(content)
                except Exception:
                    context_parts.append(r.get('content_preview', ''))
            else:
                context_parts.append(r.get('content_preview', ''))

            context_parts.append("\n---\n")

        return "".join(context_parts)

    def save_context(self, query: str, context: str, session_id: str = "default") -> str:
        """Save context to file for later retrieval.

        Args:
            query: The query that generated the context
            context: The context string
            session_id: Session identifier

        Returns:
            Path to saved context file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"context_{session_id}_{timestamp}.md"
        filepath = self.context_dir / filename

        filepath.write_text(f"<!-- Query: {query} -->\n\n{context}", encoding="utf-8")
        return str(filepath)

    def load_context(self, session_id: str = "default") -> str | None:
        """Load most recent context for a session.

        Args:
            session_id: Session identifier

        Returns:
            Context content or None if not found
        """
        context_files = sorted(self.context_dir.glob(f"context_{session_id}_*.md"), reverse=True)
        if not context_files:
            return None
        return context_files[0].read_text(encoding="utf-8")

    def clear_contexts(self, session_id: str | None = None):
        """Clear saved contexts.

        Args:
            session_id: If provided, only clear for specific session
        """
        if session_id:
            pattern = f"context_{session_id}_*.md"
        else:
            pattern = "context_*.md"

        for f in self.context_dir.glob(pattern):
            f.unlink()
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(agent): add ContextInjector class

- Get relevant context for queries
- Save/load contexts for sessions
- Support full content or preview mode
"
```

---

### Task 2.2: 上下文测试

**Files:**
- Create: `tests/test_context_injector.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for context injector."""

import pytest
from src.agent.context_injector import ContextInjector


class TestContextInjector:
    """Test ContextInjector class."""

    @pytest.fixture
    def injector(self, tmp_path):
        """Create ContextInjector instance."""
        return ContextInjector(knowledge_root=tmp_path)

    def test_get_context(self, injector):
        """Test getting context for query."""
        context = injector.get_context("测试查询", max_notes=3)
        assert isinstance(context, str)

    def test_save_and_load_context(self, injector):
        """Test saving and loading context."""
        context = "# Test Context\n\nSome content."
        path = injector.save_context("测试", context, "test_session")

        loaded = injector.load_context("test_session")
        assert loaded is not None
        assert "测试查询" in loaded or "Test Context" in loaded

    def test_clear_contexts(self, injector):
        """Test clearing contexts."""
        injector.save_context("测试 1", "Content 1", "test_session")
        injector.save_context("测试 2", "Content 2", "test_session")
        
        injector.clear_contexts("test_session")
        
        loaded = injector.load_context("test_session")
        assert loaded is None
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "test(agent): add ContextInjector tests
"
```

---

## Module 3: Task Delegate (任务委托)

### Task 3.1: 任务委托模块

**Files:**
- Create: `src/agent/task_delegate.py`

- [ ] **Step 1: 创建 TaskDelegate 类**

```python
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
        self.rag_qa = RAGQA(
            embedder=None,  # Will be initialized when needed
            vector_store=None,
            model=self.config.settings.get("retriever", {}).get("rag", {}).get("model", "qwen3.5-plus")
        )

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
        # Initialize RAG if needed
        if self.rag_qa.vector_store is None:
            from ..retriever.embedder import Embedder
            from ..retriever.vector_store import VectorStore
            
            embedder = Embedder(api_key=self.config.bailian_api_key)
            vector_store = VectorStore(
                dimension=1536,
                index_path=self.config.settings.get("retriever", {}).get("index_path")
            )
            self.rag_qa.embedder = embedder
            self.rag_qa.vector_store = vector_store

        # Get answer with context
        result = self.rag_qa.answer(topic, top_k=5 * depth)

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
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(agent): add TaskDelegate class

- Scrape and process URLs
- Fetch and summarize RSS feeds
- Research topics using knowledge base
- List available capabilities
"
```

---

## Module 4: FastAPI Server (API 服务)

### Task 4.1: FastAPI 应用

**Files:**
- Create: `src/server/__init__.py`
- Create: `src/server/app.py`

- [ ] **Step 1: 创建包初始化**

```python
"""Server module for knowledge API."""

from .app import create_app

__all__ = ["create_app"]
```

- [ ] **Step 2: 创建 FastAPI 应用**

```python
"""FastAPI application for knowledge API."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .routes import search_router, qa_router, context_router, delegate_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Personal Knowledge API",
        description="API for personal knowledge base access and management",
        version="1.0.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
    app.include_router(qa_router, prefix="/api/v1/qa", tags=["Q&A"])
    app.include_router(context_router, prefix="/api/v1/context", tags=["Context"])
    app.include_router(delegate_router, prefix="/api/v1/delegate", tags=["Delegate"])

    @app.get("/")
    def root():
        return {
            "name": "Personal Knowledge API",
            "version": "1.0.0",
            "docs": "/docs"
        }

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    return app
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(server): add FastAPI application

- Create FastAPI app with CORS
- Include API routers
- Health check endpoint
"
```

---

### Task 4.2: API 路由

**Files:**
- Create: `src/server/routes.py`

- [ ] **Step 1: 创建路由定义**

```python
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
def answer(request: QAResponse):
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
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(server): add API routes

- Search endpoints
- Q&A endpoints
- Context management endpoints
- Task delegation endpoints
"
```

---

### Task 4.3: 服务启动脚本

**Files:**
- Create: `scripts/run_server.py`

- [ ] **Step 1: 创建启动脚本**

```python
#!/usr/bin/env python3
"""Run knowledge API server."""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Knowledge API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    uvicorn.run(
        "src.server.app:create_app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=True
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(scripts): add run_server.py

- Start FastAPI server with uvicorn
- Support --host, --port, --reload options
"
```

---

### Task 4.4: 更新依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 添加新依赖**

```txt
# Phase 4: Agent integration
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
pydantic>=2.5.0
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "chore: add Phase 4 dependencies

- fastapi, uvicorn for API server
- pydantic for request validation
"
```

---

## Module 5: Integration (集成)

### Task 5.1: Claude 上下文加载脚本

**Files:**
- Create: `scripts/claude_context.py`

- [ ] **Step 1: 创建脚本**

```python
#!/usr/bin/env python3
"""Load knowledge context for Claude sessions.

Usage:
    # Get context for a topic
    python scripts/claude_context.py "机器学习"

    # Load saved context for session
    python scripts/claude_context.py --load --session my_session

    # Save context for later
    python scripts/claude_context.py "深度学习" --save --session dl_session
"""

import argparse
from src.agent.context_injector import ContextInjector


def main():
    parser = argparse.ArgumentParser(description="Claude context loader")
    parser.add_argument("query", nargs="?", help="Query to get context for")
    parser.add_argument("--load", action="store_true", help="Load saved context")
    parser.add_argument("--save", action="store_true", help="Save context")
    parser.add_argument("--session", default="default", help="Session ID")
    parser.add_argument("--full", action="store_true", help="Include full content")
    args = parser.parse_args()

    injector = ContextInjector()

    if args.load:
        context = injector.load_context(args.session)
        if context:
            print(context)
        else:
            print(f"No saved context found for session: {args.session}")
    elif args.query:
        context = injector.get_context(args.query, max_notes=5, include_full_content=args.full)
        print(context)
        
        if args.save:
            path = injector.save_context(args.query, context, args.session)
            print(f"\nContext saved to: {path}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(scripts): add claude_context.py

- Load knowledge context for Claude sessions
- Save/load contexts by session ID
- Support full content or preview mode
"
```

---

### Task 5.2: 集成测试

**Files:**
- Create: `tests/test_phase4_integration.py`

- [ ] **Step 1: 创建集成测试**

```python
"""Phase 4 integration tests."""

import pytest
from src.agent.knowledge_api import KnowledgeAPI
from src.agent.context_injector import ContextInjector
from src.agent.task_delegate import TaskDelegate


class TestPhase4:
    """Test Phase 4 integration."""

    @pytest.fixture
    def api(self):
        return KnowledgeAPI()

    @pytest.fixture
    def injector(self, tmp_path):
        return ContextInjector(knowledge_root=tmp_path)

    @pytest.fixture
    def delegate(self, tmp_path):
        return TaskDelegate(knowledge_root=tmp_path)

    def test_knowledge_api_search(self, api):
        """Test KnowledgeAPI search."""
        results = api.search("测试", top_k=3)
        assert isinstance(results, list)

    def test_knowledge_api_answer(self, api):
        """Test KnowledgeAPI Q&A."""
        result = api.answer("测试问题")
        assert "answer" in result

    def test_context_injector(self, injector):
        """Test ContextInjector."""
        context = injector.get_context("测试")
        assert isinstance(context, str)

        path = injector.save_context("测试", context, "test")
        assert path is not None

        loaded = injector.load_context("test")
        assert loaded is not None

    def test_task_delegate_capabilities(self, delegate):
        """Test TaskDelegate capabilities."""
        caps = delegate.get_available_capabilities()
        assert len(caps) > 0

    def test_task_delegate_research(self, delegate):
        """Test TaskDelegate research."""
        result = delegate.research_topic("人工智能", depth=1)
        assert "topic" in result
        assert "answer" in result
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "test: add Phase 4 integration tests
"
```

---

### Task 5.3: 更新文档

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README**

```markdown
## 实施阶段

- [x] Phase 1: 基础结构 + 手动采集 + 自动摘要
- [x] Phase 2: 自动采集 + 知识图谱
- [x] Phase 3: 语义检索 + RAG 问答
- [x] Phase 4: Agent 深度集成
  - [x] 知识 API 服务
  - [x] 上下文注入器
  - [x] 任务委托模块
  - [x] FastAPI 服务器
  - [x] Claude 上下文加载
  - [x] 集成测试

## Phase 4 功能

### 启动 API 服务

```bash
# 启动服务器
python scripts/run_server.py --port 8000 --reload

# 访问 API 文档
open http://localhost:8000/docs
```

### API 端点

| 端点 | 功能 |
|------|------|
| `POST /api/v1/search` | 语义搜索 |
| `POST /api/v1/qa` | RAG 问答 |
| `POST /api/v1/context/get` | 获取上下文 |
| `POST /api/v1/delegate/scrape` | 委托爬取任务 |
| `POST /api/v1/delegate/research` | 委托研究任务 |

### Claude 上下文加载

```bash
# 获取主题上下文
python scripts/claude_context.py "机器学习"

# 保存上下文供后续使用
python scripts/claude_context.py "深度学习" --save --session dl

# 加载已保存的上下文
python scripts/claude_context.py --load --session dl
```

### 能力列表

- **知识 API**: 外部系统可通过 REST API 访问知识库
- **上下文注入**: Claude 会话自动加载相关知识上下文
- **任务委托**: 将复杂任务委托给系统处理
- **长期记忆**: 知识库作为 Agent 的持久化记忆
```

- [ ] **Step 2: Final Phase 4 commit**

```bash
git add -A
git commit -m "docs: mark Phase 4 as complete

- Update README with Phase 4 features
- Add API usage examples
- Document Claude context integration
"
```

---

## Self-Review

### Spec Coverage

| Spec Requirement | Implementing Task |
|------------------|-------------------|
| 知识 API 服务 | Task 1.1, 1.2 |
| 上下文注入器 | Task 2.1, 2.2 |
| 任务委托模块 | Task 3.1 |
| FastAPI 服务器 | Task 4.1, 4.2, 4.3 |
| 依赖更新 | Task 4.4 |
| Claude 上下文脚本 | Task 5.1 |
| 集成测试 | Task 5.2 |
| 文档更新 | Task 5.3 |

### Checklist

- [ ] 所有文件路径已指定
- [ ] 所有代码片段已提供
- [ ] 测试用例完整
- [ ] 无占位符 (TBD/TODO)

---

## Execution Options

**Plan complete and saved to `docs/superpowers/plans/2026-04-05-personal-knowledge-base-phase4.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
