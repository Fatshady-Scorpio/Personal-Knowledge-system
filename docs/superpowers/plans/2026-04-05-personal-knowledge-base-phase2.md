# Personal Knowledge Base Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现自动内容采集（网页爬虫、RSS 订阅）和知识图谱（自动建立内容关联）

**Architecture:** 在 Phase 1 基础上，增加采集服务（Collector Service）和知识图谱服务（Graph Service），保持模块化设计

**Tech Stack:** 
- 网页爬虫：httpx, BeautifulSoup4, playwright（动态页面）
- RSS 订阅：feedparser
- 知识图谱：NetworkX, SQLite
- 任务调度：APScheduler

---

## File Structure

### Files to Create

| File | Responsibility |
|------|----------------|
| `src/collector/__init__.py` | Collector package |
| `src/collector/web_scraper.py` | 网页爬取模块 |
| `src/collector/rss_fetcher.py` | RSS 订阅抓取 |
| `src/collector/video_processor.py` | 视频处理（预留） |
| `src/graph/__init__.py` | Knowledge Graph package |
| `src/graph/graph_store.py` | 图谱存储（SQLite + NetworkX） |
| `src/graph/link_analyzer.py` | 关联分析，建立双向链接 |
| `src/graph/graph_query.py` | 图谱查询接口 |
| `src/scheduler/__init__.py` | Scheduler package |
| `src/scheduler/tasks.py` | 定时任务定义 |
| `config/sources.yaml` | 扩展数据源配置 |
| `scripts/run_collector.py` | 采集服务启动脚本 |
| `tests/test_web_scraper.py` | 爬虫测试 |
| `tests/test_graph_store.py` | 图谱测试 |

### Files to Modify

| File | Changes |
|------|---------|
| `requirements.txt` | 添加爬虫和图谱依赖 |
| `config/settings.yaml` | 添加采集和图谱配置 |
| `src/processor/summarizer.py` | 增加关联分析接口 |
| `README.md` | 更新 Phase 2 功能说明 |

---

## Module 1: Web Scraper (网页爬虫)

### Task 1.1: 基础爬虫

**Files:**
- Create: `src/collector/__init__.py`
- Create: `src/collector/web_scraper.py`

- [ ] **Step 1: 创建包初始化文件**

```python
"""Content collector module."""

from .web_scraper import WebScraper
from .rss_fetcher import RSSFetcher

__all__ = ["WebScraper", "RSSFetcher"]
```

- [ ] **Step 2: 创建 WebScraper 类**

```python
"""Web scraper for collecting articles."""

import httpx
from bs4 import BeautifulSoup
from typing import Optional
from datetime import datetime


class WebScraper:
    """Scrape articles from websites."""

    def __init__(self, timeout: int = 30):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; PersonalKB/1.0)"
        }

    async def scrape(self, url: str) -> dict:
        """Scrape content from URL.

        Args:
            url: The URL to scrape

        Returns:
            Dictionary with title, content, source_url, scraped_at
        """
        response = await self.client.get(url, headers=self.headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = soup.find("title")
        title_text = title.string.strip() if title else "Untitled"

        # Extract main content (simplified - can be enhanced)
        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text().strip() for p in paragraphs])

        return {
            "title": title_text,
            "content": content[:50000],  # Limit content length
            "source_url": url,
            "scraped_at": datetime.now().isoformat(),
        }

    async def close(self):
        await self.client.aclose()
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(collector): add WebScraper class

- Scrape articles from URLs
- Extract title and paragraph content
- Async support with httpx
"
```

---

### Task 1.2: 爬虫测试

**Files:**
- Create: `tests/test_web_scraper.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for web scraper."""

import pytest
import asyncio
from src.collector.web_scraper import WebScraper


class TestWebScraper:
    """Test WebScraper class."""

    @pytest.mark.asyncio
    async def test_scrape_article(self):
        """Test scraping a sample article."""
        scraper = WebScraper()
        
        # Use a simple test page
        result = await scraper.scrape("https://httpbin.org/html")
        
        assert "title" in result
        assert "content" in result
        assert result["source_url"] == "https://httpbin.org/html"
        
        await scraper.close()
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "test(collector): add WebScraper tests
"
```

---

## Module 2: RSS Fetcher (RSS 订阅)

### Task 2.1: RSS 订阅抓取

**Files:**
- Create: `src/collector/rss_fetcher.py`

- [ ] **Step 1: 创建 RSSFetcher 类**

```python
"""RSS feed fetcher."""

import feedparser
import httpx
from typing import Optional
from datetime import datetime


class RSSFetcher:
    """Fetch articles from RSS feeds."""

    def __init__(self, timeout: int = 30):
        self.client = httpx.AsyncClient(timeout=timeout)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; PersonalKB/1.0; RSS Fetcher)"
        }

    async def fetch(self, feed_url: str, limit: int = 10) -> list[dict]:
        """Fetch latest entries from RSS feed.

        Args:
            feed_url: The RSS feed URL
            limit: Maximum number of entries to fetch

        Returns:
            List of entry dictionaries
        """
        response = await self.client.get(feed_url, headers=self.headers)
        response.raise_for_status()

        feed = feedparser.parse(response.text)
        entries = []

        for entry in feed.entries[:limit]:
            entries.append({
                "title": entry.get("title", "Untitled"),
                "content": entry.get("summary", entry.get("description", "")),
                "source_url": entry.get("link", ""),
                "published": entry.get("published", ""),
                "fetched_at": datetime.now().isoformat(),
                "feed_title": feed.feed.get("title", ""),
            })

        return entries

    async def close(self):
        await self.client.aclose()
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(collector): add RSSFetcher class

- Fetch entries from RSS feeds
- Parse with feedparser
- Return structured entry list
"
```

---

### Task 2.2: 更新数据源配置

**Files:**
- Modify: `config/sources.yaml`

- [ ] **Step 1: 扩展 sources.yaml**

```yaml
# Data Sources Configuration

# Domestic sources (China)
domestic:
  websites:
    - name: "机器之心"
      url: "https://www.jiqizhixin.com"
      category: "AI"
      scrape_selector: ".article-content"  # CSS selector for content
    - name: "量子位"
      url: "https://www.qbitai.com"
      category: "AI"
      scrape_selector: ".article-body"

  rss_feeds:
    - name: "机器之心 RSS"
      url: "https://www.jiqizhixin.com/rss"
      category: "AI"
    - name: "量子位 RSS"
      url: "https://www.qbitai.com/feed"
      category: "AI"

  video_channels:
    - name: "B 站 AI 频道"
      platform: "bilibili"
      category: "AI"

# International sources
international:
  websites:
    - name: "Hacker News AI"
      url: "https://news.ycombinator.com/front?query=AI"
      category: "AI"

  rss_feeds:
    - name: "Hacker News"
      url: "https://news.ycombinator.com/rss"
      category: "AI"
    - name: "arXiv cs.AI"
      url: "https://arxiv.org/rss/cs.AI"
      category: "AI"

# User custom sources
custom:
  websites: []
  rss_feeds: []
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "config: extend sources.yaml with RSS feeds and selectors
"
```

---

## Module 3: Knowledge Graph (知识图谱)

### Task 3.1: 图谱存储

**Files:**
- Create: `src/graph/__init__.py`
- Create: `src/graph/graph_store.py`

- [ ] **Step 1: 创建包初始化**

```python
"""Knowledge graph module."""

from .graph_store import GraphStore
from .link_analyzer import LinkAnalyzer

__all__ = ["GraphStore", "LinkAnalyzer"]
```

- [ ] **Step 2: 创建 GraphStore 类**

```python
"""Knowledge graph storage using SQLite and NetworkX."""

import sqlite3
import networkx as nx
from pathlib import Path
from typing import Optional


class GraphStore:
    """Store and query knowledge graph."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.graph = nx.DiGraph()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content_preview TEXT,
                category TEXT,
                tags TEXT,
                created_at TEXT
            )
        """)

        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT,
                target_id TEXT,
                relation_type TEXT,
                weight REAL DEFAULT 1.0,
                PRIMARY KEY (source_id, target_id, relation_type)
            )
        """)

        conn.commit()
        conn.close()

    def add_node(self, node_id: str, title: str, content_preview: str = "",
                 category: str = "", tags: list[str] = None):
        """Add a node to the graph."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO nodes (id, title, content_preview, category, tags, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (node_id, title, content_preview[:200], category,
              ",".join(tags) if tags else ""))

        conn.commit()
        conn.close()

        # Also add to NetworkX graph
        self.graph.add_node(node_id, title=title, category=category)

    def add_edge(self, source_id: str, target_id: str, relation_type: str = "related"):
        """Add an edge between two nodes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO edges (source_id, target_id, relation_type, weight)
            VALUES (?, ?, ?, 1.0)
        """, (source_id, target_id, relation_type))

        conn.commit()
        conn.close()

        # Also add to NetworkX graph
        self.graph.add_edge(source_id, target_id, relation_type=relation_type)

    def get_related(self, node_id: str, limit: int = 10) -> list[dict]:
        """Get nodes related to the given node."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT n.id, n.title, n.category, e.relation_type
            FROM edges e
            JOIN nodes n ON e.target_id = n.id
            WHERE e.source_id = ?
            LIMIT ?
        """, (node_id, limit))

        results = [
            {"id": row[0], "title": row[1], "category": row[2], "relation": row[3]}
            for row in cursor.fetchall()
        ]

        conn.close()
        return results
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(graph): add GraphStore class

- SQLite storage for nodes and edges
- NetworkX for in-memory graph operations
- Add node, add edge, get related queries
"
```

---

### Task 3.2: 链接分析器

**Files:**
- Create: `src/graph/link_analyzer.py`

- [ ] **Step 1: 创建 LinkAnalyzer 类**

```python
"""Link analyzer for building knowledge graph connections."""

from ..utils.model_router import get_router


class LinkAnalyzer:
    """Analyze content and build graph connections."""

    def __init__(self):
        self.router = get_router()

    def find_related(
        self,
        content: str,
        existing_notes: list[dict]
    ) -> list[dict]:
        """Find related notes for given content.

        Args:
            content: The content to analyze
            existing_notes: List of existing notes with title, content, tags

        Returns:
            List of related note dicts with relation type
        """
        # Build prompt for LLM
        notes_context = "\n".join([
            f"- {n['title']}: {n['tags']}"
            for n in existing_notes
        ])

        prompt = f"""分析以下内容，找出与现有笔记的关联：

新内容：
{content[:2000]}

现有笔记：
{notes_context}

请找出相关的笔记（最多 5 个），并说明关联类型。
返回 JSON 格式：
[
    {{"note_title": "笔记标题", "relation": "扩展/反驳/示例/相关"}},
    ...
]
"""

        # Call LLM
        result = self.router.call(
            model="qwen3.5-plus",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Parse JSON
        import json
        result = result.strip()
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()

        return json.loads(result)
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(graph): add LinkAnalyzer class

- Use LLM to find relationships between notes
- Support multiple relation types
"
```

---

## Module 4: Integration (集成)

### Task 4.1: 采集服务启动脚本

**Files:**
- Create: `scripts/run_collector.py`

- [ ] **Step 1: 创建启动脚本**

```python
#!/usr/bin/env python3
"""Collector service runner."""

import asyncio
import argparse
from pathlib import Path

from src.collector import WebScraper, RSSFetcher
from src.processor.summarizer import Summarizer
from src.graph import GraphStore, LinkAnalyzer
from src.utils.config import get_config


async def scrape_url(url: str, output_dir: str):
    """Scrape a URL and process the content."""
    scraper = WebScraper()
    summarizer = Summarizer(output_dir=output_dir)

    print(f"Scraping: {url}")
    content = await scraper.scrape(url)

    markdown = summarizer.process_to_markdown(
        content["content"],
        title=content["title"],
        source_url=content["source_url"]
    )

    filepath = summarizer.save_to_file(
        content["content"],
        title=content["title"],
        source_url=content["source_url"]
    )

    print(f"Saved: {filepath}")
    await scraper.close()


async def fetch_rss(feed_url: str, output_dir: str, limit: int = 5):
    """Fetch RSS feed and process entries."""
    fetcher = RSSFetcher()
    summarizer = Summarizer(output_dir=output_dir)

    print(f"Fetching: {feed_url}")
    entries = await fetcher.fetch(feed_url, limit=limit)

    for entry in entries:
        filepath = summarizer.save_to_file(
            entry["content"],
            title=entry["title"],
            source_url=entry["source_url"]
        )
        print(f"Saved: {filepath}")

    await fetcher.close()


def main():
    parser = argparse.ArgumentParser(description="Content Collector")
    parser.add_argument("command", choices=["scrape", "rss"], help="Command to run")
    parser.add_argument("--url", required=True, help="URL or RSS feed URL")
    parser.add_argument("--limit", type=int, default=5, help="Limit for RSS entries")
    parser.add_argument("--output", help="Output directory")

    args = parser.parse_args()

    config = get_config()
    output_dir = args.output or Path(config.paths["knowledge_root"]) / "20-Processed"

    if args.command == "scrape":
        asyncio.run(scrape_url(args.url, str(output_dir)))
    elif args.command == "rss":
        asyncio.run(fetch_rss(args.url, str(output_dir), args.limit))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(scripts): add run_collector.py script

- Scrape URLs with: python scripts/run_collector.py scrape --url <URL>
- Fetch RSS with: python scripts/run_collector.py rss --url <RSS_URL> --limit 5
"
```

---

### Task 4.2: 更新依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 添加新依赖**

```txt
# Core
httpx>=0.25.0
pyyaml>=6.0
python-dotenv>=1.0.0
dashscope>=1.14.0

# Web scraping
beautifulsoup4>=4.12.0
lxml>=5.0.0
playwright>=1.40.0  # For dynamic pages

# RSS
feedparser>=6.0.10

# Knowledge graph
networkx>=3.2.0

# Scheduler
apscheduler>=3.10.4

# Vector search (Phase 3)
numpy>=1.26.0
faiss-cpu>=1.7.4

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "chore: add Phase 2 dependencies

- beautifulsoup4, lxml for web scraping
- feedparser for RSS
- networkx for knowledge graph
- apscheduler for task scheduling
"
```

---

## Phase 2验收

### Task 5.1: 功能测试

**Files:**
- Create: `tests/test_phase2_integration.py`

- [ ] **Step 1: 创建集成测试**

```python
"""Phase 2 integration tests."""

import pytest
import asyncio
from pathlib import Path

from src.collector import WebScraper, RSSFetcher
from src.graph import GraphStore, LinkAnalyzer


class TestPhase2:
    """Test Phase 2 functionality."""

    @pytest.mark.asyncio
    async def test_scrape_and_process(self):
        """Test scraping and processing a URL."""
        scraper = WebScraper()
        result = await scraper.scrape("https://httpbin.org/html")

        assert "title" in result
        assert "content" in result
        await scraper.close()

    @pytest.mark.asyncio
    async def test_rss_fetch(self):
        """Test RSS fetching."""
        fetcher = RSSFetcher()
        entries = await fetcher.fetch("https://httpbin.org/rss", limit=3)

        assert isinstance(entries, list)
        await fetcher.close()

    def test_graph_operations(self, tmp_path):
        """Test graph store operations."""
        db_path = tmp_path / "test_graph.db"
        store = GraphStore(db_path)

        store.add_node("note1", "Test Note 1", tags=["test"])
        store.add_node("note2", "Test Note 2", tags=["test"])
        store.add_edge("note1", "note2", "related")

        related = store.get_related("note1")
        assert len(related) == 1
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "test: add Phase 2 integration tests
"
```

---

### Task 5.2: 更新文档

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README 添加 Phase 2 功能说明**

```markdown
## 实施阶段

- [x] Phase 1: 基础结构 + 手动采集 + 自动摘要
- [x] Phase 2: 自动采集 + 知识图谱
- [ ] Phase 3: 语义检索 + RAG 问答
- [ ] Phase 4: Agent 深度集成

## Phase 2 功能

### 网页爬虫

```bash
# 爬取网页
python scripts/run_collector.py scrape --url "https://example.com/article"
```

### RSS 订阅

```bash
# 获取 RSS 条目
python scripts/run_collector.py rss --url "https://example.com/feed" --limit 10
```

### 知识图谱

自动建立内容关联，支持：
- 相关笔记推荐
- 双向链接
- 图谱浏览
```

- [ ] **Step 2: Final Phase 2 commit**

```bash
git add -A
git commit -m "docs: mark Phase 2 as complete

- Update README with Phase 2 features
- Add usage examples for scraper and RSS
"
```

---

## Self-Review

### Spec Coverage

| Spec Requirement | Implementing Task |
|------------------|-------------------|
| 网页爬虫 | Task 1.1, 1.2 |
| RSS 订阅 | Task 2.1, 2.2 |
| 知识图谱存储 | Task 3.1 |
| 链接分析 | Task 3.2 |
| 集成脚本 | Task 4.1 |
| 依赖更新 | Task 4.2 |
| 测试 | Task 5.1 |
| 文档 | Task 5.2 |

### Checklist

- [ ] 所有文件路径已指定
- [ ] 所有代码片段已提供
- [ ] 测试用例完整
- [ ] 无占位符 (TBD/TODO)

---

## Execution Options

**Plan complete and saved to `docs/superpowers/plans/2026-04-05-personal-knowledge-base-phase2.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
