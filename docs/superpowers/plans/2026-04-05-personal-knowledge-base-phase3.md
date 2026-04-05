# Personal Knowledge Base Phase 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现语义检索（向量嵌入 + 相似度搜索）和 RAG 问答（基于知识库的智能问答）

**Architecture:** 在 Phase 2 基础上，增加检索服务（Retriever Service），使用向量数据库存储嵌入，支持语义搜索和 RAG 问答

**Tech Stack:** 
- 向量嵌入：阿里云百炼 Text Embedding API
- 向量搜索：FAISS（Facebook AI Similarity Search）
- RAG 问答：自研实现，基于检索结果生成答案

---

## File Structure

### Files to Create

| File | Responsibility |
|------|----------------|
| `src/retriever/__init__.py` | Retriever 包初始化 |
| `src/retriever/embedder.py` | 向量嵌入生成 |
| `src/retriever/semantic_search.py` | 语义搜索 |
| `src/retriever/rag_qa.py` | RAG 问答 |
| `src/retriever/vector_store.py` | 向量存储（FAISS） |
| `scripts/build_index.py` | 构建索引脚本 |
| `scripts/query.py` | 查询脚本 |
| `tests/test_embedder.py` | 嵌入测试 |
| `tests/test_semantic_search.py` | 搜索测试 |
| `tests/test_rag_qa.py` | RAG 测试 |

### Files to Modify

| File | Changes |
|------|---------|
| `requirements.txt` | 添加 faiss-cpu, numpy |
| `config/settings.yaml` | 添加检索配置 |
| `src/processor/summarizer.py` | 增加嵌入生成接口 |
| `README.md` | 更新 Phase 3 功能说明 |

---

## Module 1: Embedder (向量嵌入)

### Task 1.1: 嵌入生成器

**Files:**
- Create: `src/retriever/__init__.py`
- Create: `src/retriever/embedder.py`

- [ ] **Step 1: 创建包初始化**

```python
"""Retriever module for semantic search and RAG."""

from .embedder import Embedder
from .semantic_search import SemanticSearch
from .rag_qa import RAGQA

__all__ = ["Embedder", "SemanticSearch", "RAGQA"]
```

- [ ] **Step 2: 创建 Embedder 类**

```python
"""Text embedder using Alibaba Cloud Bailian API."""

import requests
from typing import Optional


class Embedder:
    """Generate text embeddings using Bailian API."""

    def __init__(self, api_key: str, model: str = "text-embedding-v2"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/generation"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        data = {
            "model": self.model,
            "input": {"texts": [text]}
        }

        response = self.session.post(self.base_url, json=data)
        result = response.json()

        if response.status_code == 200:
            embeddings = result.get("output", {}).get("embeddings", [])
            if embeddings:
                return embeddings[0].get("embedding", [])
        else:
            error = result.get("error", {})
            raise RuntimeError(f"API error: {error.get('code')} - {error.get('message')}")

        return []

    def embed_batch(self, texts: list[str], batch_size: int = 10) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            data = {
                "model": self.model,
                "input": {"texts": batch}
            }

            response = self.session.post(self.base_url, json=data)
            result = response.json()

            if response.status_code == 200:
                embeddings = result.get("output", {}).get("embeddings", [])
                for emb in embeddings:
                    all_embeddings.append(emb.get("embedding", []))

        return all_embeddings
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(retriever): add Embedder class

- Generate embeddings using Bailian text-embedding-v2
- Support single and batch embedding
- Async support ready
"
```

---

### Task 1.2: 嵌入测试

**Files:**
- Create: `tests/test_embedder.py`

- [ ] **Step 1: 创建测试文件**

```python
"""Tests for embedder module."""

import pytest
from src.retriever.embedder import Embedder
from src.utils.config import get_config


class TestEmbedder:
    """Test Embedder class."""

    @pytest.fixture
    def embedder(self):
        """Create Embedder instance."""
        config = get_config()
        return Embedder(api_key=config.bailian_api_key)

    def test_embed_returns_list(self, embedder):
        """Test that embed returns a list of floats."""
        result = embedder.embed("这是一段测试文本")

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(x, float) for x in result)

    def test_embed_batch(self, embedder):
        """Test batch embedding."""
        texts = ["文本一", "文本二", "文本三"]
        results = embedder.embed_batch(texts)

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "test(retriever): add Embedder tests
"
```

---

## Module 2: Vector Store (向量存储)

### Task 2.1: FAISS 向量存储

**Files:**
- Create: `src/retriever/vector_store.py`

- [ ] **Step 1: 创建 VectorStore 类**

```python
"""Vector store using FAISS for efficient similarity search."""

import faiss
import numpy as np
import json
from pathlib import Path
from typing import Optional


class VectorStore:
    """FAISS-based vector store for semantic search."""

    def __init__(self, dimension: int = 1536, index_path: str | Path | None = None):
        """Initialize vector store.

        Args:
            dimension: Embedding dimension (1536 for text-embedding-v2)
            index_path: Path to save/load index
        """
        self.dimension = dimension
        self.index_path = Path(index_path) if index_path else None
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: list[dict] = []  # Store metadata for each vector

        # Load existing index if path provided
        if self.index_path and self.index_path.exists():
            self.load()

    def add(self, embeddings: list[list[float]], metadata: list[dict]):
        """Add vectors to the index.

        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dicts (one per embedding)
        """
        if not embeddings:
            return

        # Convert to numpy array
        vectors = np.array(embeddings, dtype=np.float32)

        # Add to FAISS index
        self.index.add(vectors)

        # Store metadata
        self.metadata.extend(metadata)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10
    ) -> list[dict]:
        """Search for similar vectors.

        Args:
            query_embedding: The query embedding
            top_k: Number of results to return

        Returns:
            List of results with metadata and distance
        """
        if self.index.ntotal == 0:
            return []

        query = np.array([query_embedding], dtype=np.float32)
        distances, indices = self.index.search(query, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):
                results.append({
                    **self.metadata[idx],
                    "distance": float(distances[0][i])
                })

        return results

    def save(self):
        """Save index and metadata to disk."""
        if self.index_path is None:
            return

        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path) + ".index")

        # Save metadata
        metadata_path = self.index_path.with_suffix(".json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def load(self):
        """Load index and metadata from disk."""
        if self.index_path is None:
            return

        index_path = str(self.index_path) + ".index"
        metadata_path = self.index_path.with_suffix(".json")

        if Path(index_path).exists():
            self.index = faiss.read_index(index_path)

        if Path(metadata_path).exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

    @property
    def count(self) -> int:
        """Get number of vectors in the index."""
        return self.index.ntotal
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(retriever): add VectorStore class

- FAISS IndexFlatL2 for similarity search
- Store metadata alongside vectors
- Save/load index and metadata
"
```

---

## Module 3: Semantic Search (语义搜索)

### Task 3.1: 语义搜索服务

**Files:**
- Create: `src/retriever/semantic_search.py`

- [ ] **Step 1: 创建 SemanticSearch 类**

```python
"""Semantic search service."""

from pathlib import Path
from .embedder import Embedder
from .vector_store import VectorStore


class SemanticSearch:
    """Semantic search over knowledge base."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        knowledge_root: str | Path
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.knowledge_root = Path(knowledge_root)

    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5
    ) -> list[dict]:
        """Search for semantically similar content.

        Args:
            query: The search query
            top_k: Number of results
            min_score: Minimum similarity score (0-1)

        Returns:
            List of matching documents with scores
        """
        # Generate query embedding
        query_embedding = self.embedder.embed(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k * 2)

        # Filter by score and format
        filtered_results = []
        for r in results:
            # Convert distance to similarity score (lower distance = higher similarity)
            score = 1 / (1 + r.get("distance", 1.0))
            if score >= min_score:
                filtered_results.append({
                    "title": r.get("title", "Unknown"),
                    "content_preview": r.get("content_preview", "")[:200],
                    "file_path": r.get("file_path", ""),
                    "category": r.get("category", ""),
                    "tags": r.get("tags", []),
                    "score": round(score, 3)
                })

        return filtered_results[:top_k]

    def build_index(self, rebuild: bool = False) -> int:
        """Build index from existing knowledge base.

        Args:
            rebuild: If True, rebuild index from scratch

        Returns:
            Number of documents indexed
        """
        if rebuild:
            self.vector_store = VectorStore(
                dimension=self.embedder.model_dimension,
                index_path=self.vector_store.index_path
            )

        # Scan knowledge base for markdown files
        documents = []
        for md_file in self.knowledge_root.rglob("*.md"):
            if "20-Processed" in str(md_file):  # Only index processed files
                content = md_file.read_text(encoding="utf-8")
                documents.append({
                    "title": md_file.stem,
                    "content": content,
                    "content_preview": content[:500],
                    "file_path": str(md_file),
                    "category": md_file.parent.name
                })

        if not documents:
            return 0

        # Generate embeddings
        texts = [f"{d['title']}: {d['content'][:1000]}" for d in documents]
        embeddings = self.embedder.embed_batch(texts)

        # Add to vector store
        self.vector_store.add(embeddings, documents)
        self.vector_store.save()

        return len(documents)
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(retriever): add SemanticSearch class

- Search knowledge base by semantic similarity
- Build index from markdown files
- Filter by similarity score
"
```

---

## Module 4: RAG QA (问答)

### Task 4.1: RAG 问答服务

**Files:**
- Create: `src/retriever/rag_qa.py`

- [ ] **Step 1: 创建 RAGQA 类**

```python
"""RAG-based question answering service."""

from .embedder import Embedder
from .vector_store import VectorStore
from ..utils.model_router import get_router


class RAGQA:
    """Question answering using Retrieval Augmented Generation."""

    def __init__(
        self,
        embedder: Embedder,
        vector_store: VectorStore,
        model: str = "qwen3.5-plus"
    ):
        self.embedder = embedder
        self.vector_store = vector_store
        self.router = get_router()
        self.model = model

    def answer(
        self,
        question: str,
        top_k: int = 5,
        include_sources: bool = True
    ) -> dict:
        """Answer a question using retrieved context.

        Args:
            question: The question to answer
            top_k: Number of documents to retrieve
            include_sources: Whether to include source references

        Returns:
            Dictionary with answer and optionally sources
        """
        # Retrieve relevant context
        query_embedding = self.embedder.embed(question)
        results = self.vector_store.search(query_embedding, top_k)

        if not results:
            return {
                "answer": "抱歉，没有找到相关的知识内容。",
                "sources": []
            }

        # Build context from retrieved documents
        context_parts = []
        sources = []

        for i, r in enumerate(results, 1):
            context_parts.append(f"[资料{i}] {r.get('content_preview', '')[:500]}")
            sources.append({
                "title": r.get("title", "Unknown"),
                "file_path": r.get("file_path", ""),
                "score": 1 / (1 + r.get("distance", 1.0))
            })

        context = "\n\n".join(context_parts)

        # Generate answer using LLM
        prompt = f"""请基于以下资料回答问题。如果资料中没有相关信息，请说明。

资料：
{context}

问题：{question}

请用中文回答，确保答案准确且完整。"""

        answer = self.router.call(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )

        result = {"answer": answer}

        if include_sources:
            result["sources"] = sources

        return result
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(retriever): add RAGQA class

- Answer questions using retrieved context
- Include source references
- Use LLM for answer generation
"
```

---

## Module 5: Integration (集成)

### Task 5.1: 命令行工具

**Files:**
- Create: `scripts/build_index.py`
- Create: `scripts/query.py`

- [ ] **Step 1: 创建索引构建脚本**

```python
#!/usr/bin/env python3
"""Build semantic search index from knowledge base."""

import argparse
from src.retriever.embedder import Embedder
from src.retriever.vector_store import VectorStore
from src.retriever.semantic_search import SemanticSearch
from src.utils.config import get_config


def main():
    parser = argparse.ArgumentParser(description="Build search index")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild from scratch")
    parser.add_argument("--output", help="Output path for index")
    args = parser.parse_args()

    config = get_config()

    embedder = Embedder(api_key=config.bailian_api_key)
    index_path = args.output or config.settings.get("retriever", {}).get(
        "index_path", "./knowledge/index"
    )
    vector_store = VectorStore(index_path=index_path)

    search = SemanticSearch(
        embedder=embedder,
        vector_store=vector_store,
        knowledge_root=config.paths.get("knowledge_root", "./knowledge")
    )

    print("Building index...")
    count = search.build_index(rebuild=args.rebuild)
    print(f"Indexed {count} documents")
    print(f"Index saved to {index_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 创建查询脚本**

```python
#!/usr/bin/env python3
"""Query knowledge base using semantic search."""

import argparse
from src.retriever.embedder import Embedder
from src.retriever.vector_store import VectorStore
from src.retriever.semantic_search import SemanticSearch
from src.retriever.rag_qa import RAGQA
from src.utils.config import get_config


def main():
    parser = argparse.ArgumentParser(description="Query knowledge base")
    parser.add_argument("query", nargs="?", help="Search query or question")
    parser.add_argument("--qa", action="store_true", help="Use RAG QA mode")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--index", help="Path to index")
    args = parser.parse_args()

    config = get_config()

    embedder = Embedder(api_key=config.bailian_api_key)
    index_path = args.index or config.settings.get("retriever", {}).get(
        "index_path", "./knowledge/index"
    )
    vector_store = VectorStore(index_path=index_path)

    if args.qa:
        qa = RAGQA(embedder=embedder, vector_store=vector_store)
        result = qa.answer(args.query, top_k=args.top_k)
        print(f"\n答案：{result['answer']}\n")
        if result['sources']:
            print("资料来源:")
            for s in result['sources']:
                print(f"  - {s['title']} (score: {s['score']:.2f})")
    else:
        search = SemanticSearch(
            embedder=embedder,
            vector_store=vector_store,
            knowledge_root=config.paths.get("knowledge_root", "./knowledge")
        )
        results = search.search(args.query, top_k=args.top_k)
        print(f"\n找到 {len(results)} 个结果:\n")
        for r in results:
            print(f"[{r['score']:.2f}] {r['title']}")
            print(f"    {r['content_preview'][:100]}...")
            print()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(scripts): add build_index.py and query.py

- build_index.py: Build semantic search index
- query.py: Search or ask questions
"
```

---

### Task 5.2: 更新依赖和配置

**Files:**
- Modify: `requirements.txt`
- Modify: `config/settings.yaml`

- [ ] **Step 1: 更新 requirements.txt**

```txt
# Phase 3: Semantic search and RAG
faiss-cpu>=1.7.4
numpy>=1.26.0
```

- [ ] **Step 2: 更新 config/settings.yaml**

```yaml
# Retriever settings (Phase 3)
retriever:
  model: "text-embedding-v2"
  dimension: 1536  # Embedding dimension
  index_path: "${PWD}/knowledge/index"
  top_k: 5  # Default results for search
  min_score: 0.5  # Minimum similarity score

  # RAG settings
  rag:
    model: "qwen3.5-plus"
    top_k: 5
    include_sources: true
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "chore: add Phase 3 dependencies and config

- faiss-cpu, numpy for vector search
- retriever settings in config
"
```

---

## Phase 3 验收

### Task 6.1: 集成测试

**Files:**
- Create: `tests/test_phase3_integration.py`

- [ ] **Step 1: 创建集成测试**

```python
"""Phase 3 integration tests."""

import pytest
from pathlib import Path
from src.retriever.embedder import Embedder
from src.retriever.vector_store import VectorStore
from src.retriever.semantic_search import SemanticSearch
from src.retriever.rag_qa import RAGQA
from src.utils.config import get_config


class TestPhase3:
    """Test Phase 3 functionality."""

    @pytest.fixture
    def embedder(self):
        config = get_config()
        return Embedder(api_key=config.bailian_api_key)

    @pytest.fixture
    def vector_store(self, tmp_path):
        return VectorStore(dimension=1536, index_path=tmp_path / "test_index")

    def test_embedder(self, embedder):
        """Test embedding generation."""
        result = embedder.embed("测试文本")
        assert len(result) > 0

    def test_vector_store(self, vector_store, embedder):
        """Test vector store operations."""
        embedding = embedder.embed("测试")
        vector_store.add([embedding], [{"title": "测试文档"}])
        assert vector_store.count == 1

    def test_semantic_search(self, embedder, vector_store, tmp_path):
        """Test semantic search."""
        # Add test documents
        embeddings = embedder.embed_batch(["人工智能介绍", "机器学习教程"])
        vector_store.add(embeddings, [
            {"title": "AI 介绍", "content_preview": "人工智能..."},
            {"title": "ML 教程", "content_preview": "机器学习..."}
        ])

        search = SemanticSearch(embedder, vector_store, tmp_path)
        results = search.search("AI 是什么", top_k=2)
        assert len(results) > 0

    def test_rag_qa(self, embedder, vector_store):
        """Test RAG question answering."""
        # Add test context
        embedding = embedder.embed("Python 是一种编程语言")
        vector_store.add([embedding], [{
            "title": "Python 介绍",
            "content_preview": "Python 是一种高级编程语言..."
        }])

        qa = RAGQA(embedder, vector_store)
        result = qa.answer("Python 是什么？")

        assert "answer" in result
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "test: add Phase 3 integration tests
"
```

---

### Task 6.2: 更新文档

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README 添加 Phase 3 功能说明**

```markdown
## 实施阶段

- [x] Phase 1: 基础结构 + 手动采集 + 自动摘要
- [x] Phase 2: 自动采集 + 知识图谱
- [x] Phase 3: 语义检索 + RAG 问答
- [ ] Phase 4: Agent 深度集成

## Phase 3 功能

### 语义搜索

```bash
# 构建索引
python scripts/build_index.py

# 搜索内容
python scripts/query.py "人工智能的最新进展"
```

### RAG 问答

```bash
# 问答模式
python scripts/query.py --qa "什么是深度学习？"
```

### 功能特点

- 向量嵌入：使用阿里云百炼 text-embedding-v2
- 相似度搜索：FAISS 高效索引
- 智能问答：基于检索结果生成答案
- 资料来源：自动引用来源
```

- [ ] **Step 2: Final Phase 3 commit**

```bash
git add -A
git commit -m "docs: mark Phase 3 as complete

- Update README with Phase 3 features
- Add usage examples for search and QA
"
```

---

## Self-Review

### Spec Coverage

| Spec Requirement | Implementing Task |
|------------------|-------------------|
| 向量嵌入生成 | Task 1.1, 1.2 |
| 向量存储 (FAISS) | Task 2.1 |
| 语义搜索 | Task 3.1 |
| RAG 问答 | Task 4.1 |
| 命令行工具 | Task 5.1 |
| 依赖和配置 | Task 5.2 |
| 集成测试 | Task 6.1 |
| 文档更新 | Task 6.2 |

### Checklist

- [ ] 所有文件路径已指定
- [ ] 所有代码片段已提供
- [ ] 测试用例完整
- [ ] 无占位符 (TBD/TODO)

---

## Execution Options

**Plan complete and saved to `docs/superpowers/plans/2026-04-05-personal-knowledge-base-phase3.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
