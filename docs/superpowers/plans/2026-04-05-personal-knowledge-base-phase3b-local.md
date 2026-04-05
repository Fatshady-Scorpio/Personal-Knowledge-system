# Phase 3b: 本地检索方案实施计划

**Goal:** 使用 BM25 + Ollama 本地模型替代云端 Embedding，实现完全本地的语义检索和 RAG 问答

**Architecture:** 
- **BM25**: 传统关键词检索（快速、无需训练）
- **Ollama**: 本地运行 Qwen2.5-Coder 或其他小模型生成嵌入/理解上下文
- **混合检索**: BM25 + 轻量级语义相似度

---

## File Structure

### Files to Create

| File | Responsibility |
|------|----------------|
| `src/retriever/bm25_search.py` | BM25 关键词检索 |
| `src/retriever/hybrid_search.py` | 混合检索（BM25 + 语义） |
| `src/retriever/local_embedder.py` | Ollama 本地嵌入生成 |
| `scripts/setup_ollama.sh` | Ollama 安装和配置脚本 |
| `config/ollama_config.yaml` | Ollama 配置 |

### Files to Modify

| File | Changes |
|------|---------|
| `requirements.txt` | 添加 rank-bm25, ollama |
| `config/settings.yaml` | 添加本地检索配置 |
| `scripts/build_index.py` | 支持本地索引 |
| `scripts/query.py` | 支持本地查询模式 |

---

## Module 1: BM25 检索

### Task 1.1: BM25 实现

**Files:**
- Create: `src/retriever/bm25_search.py`

- [ ] **Step 1: 创建 BM25Search 类**

```python
"""BM25 keyword search for local retrieval."""

from rank_bm25 import BM25Okapi
from pathlib import Path
from typing import Optional
import pickle


class BM25Search:
    """BM25-based keyword search over knowledge base."""

    def __init__(self, knowledge_root: str | Path):
        self.knowledge_root = Path(knowledge_root)
        self.documents: list[dict] = []
        self.bm25: Optional[BM25Okapi] = None
        self.index_path = self.knowledge_root / ".bm25_index"

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        # Simple tokenization - can be enhanced for Chinese
        import jieba
        return list(jieba.cut(text))

    def build_index(self) -> int:
        """Build BM25 index from knowledge base.

        Returns:
            Number of documents indexed
        """
        self.documents = []
        tokenized_docs = []

        # Scan markdown files
        for md_file in self.knowledge_root.rglob("*.md"):
            if "20-Processed" in str(md_file):
                content = md_file.read_text(encoding="utf-8")
                self.documents.append({
                    "title": md_file.stem,
                    "content": content,
                    "content_preview": content[:500],
                    "file_path": str(md_file),
                    "category": md_file.parent.name
                })
                tokenized_docs.append(self.tokenize(content))

        # Build BM25 index
        if tokenized_docs:
            self.bm25 = BM25Okapi(tokenized_docs)
            self.save_index()

        return len(self.documents)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search for documents matching query.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of matching documents with scores
        """
        if self.bm25 is None:
            self.load_index()

        if self.bm25 is None:
            return []

        query_tokens = self.tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                doc = self.documents[idx].copy()
                doc["score"] = float(scores[idx])
                results.append(doc)

        return results

    def save_index(self):
        """Save BM25 index to disk."""
        if self.bm25 is None:
            return

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "bm25_state": self.bm25
            }, f)

    def load_index(self):
        """Load BM25 index from disk."""
        if not self.index_path.exists():
            return

        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.bm25 = data["bm25_state"]
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(retriever): add BM25Search class

- BM25 keyword search
- Chinese tokenization with jieba
- Save/load index
"
```

---

## Module 2: Ollama 本地嵌入

### Task 2.1: Ollama 嵌入生成器

**Files:**
- Create: `src/retriever/local_embedder.py`

- [ ] **Step 1: 创建 LocalEmbedder 类**

```python
"""Local embedder using Ollama."""

import requests
from typing import Optional


class LocalEmbedder:
    """Generate embeddings using local Ollama model."""

    def __init__(self, model: str = "qwen2.5-coder:7b", ollama_url: str = "http://localhost:11434"):
        self.model = model
        self.ollama_url = ollama_url
        self.session = requests.Session()

    def check_connection(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = self.session.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def embed(self, text: str) -> list[float]:
        """Generate embedding for text using Ollama.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector
        """
        # Use Ollama embeddings API
        url = f"{self.ollama_url}/api/embeddings"
        data = {
            "model": self.model,
            "prompt": text
        }

        response = self.session.post(url, json=data, timeout=60)
        result = response.json()

        if response.status_code == 200:
            return result.get("embedding", [])
        else:
            raise RuntimeError(f"Ollama error: {result}")

    def embed_batch(self, texts: list[str], batch_size: int = 5) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch (smaller for local)

        Returns:
            List of embedding vectors
        """
        all_embeddings = []

        for text in texts:
            try:
                embedding = self.embed(text)
                if embedding:
                    all_embeddings.append(embedding)
            except Exception as e:
                print(f"Error embedding text: {e}")
                continue

        return all_embeddings
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(retriever): add LocalEmbedder class

- Generate embeddings via Ollama
- Support local Qwen2.5-Coder model
- Batch embedding with error handling
"
```

---

## Module 3: 混合检索

### Task 3.1: 混合检索器

**Files:**
- Create: `src/retriever/hybrid_search.py`

- [ ] **Step 1: 创建 HybridSearch 类**

```python
"""Hybrid search combining BM25 and semantic search."""

from pathlib import Path
from .bm25_search import BM25Search
from .local_embedder import LocalEmbedder
from .vector_store import VectorStore
import numpy as np


class HybridSearch:
    """Hybrid search combining keyword and semantic search."""

    def __init__(
        self,
        knowledge_root: str | Path,
        use_semantic: bool = True,
        bm25_weight: float = 0.5,
        semantic_weight: float = 0.5
    ):
        self.knowledge_root = Path(knowledge_root)
        self.use_semantic = use_semantic
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight

        # Initialize BM25
        self.bm25 = BM25Search(knowledge_root)

        # Initialize semantic search if enabled
        if use_semantic:
            self.embedder = LocalEmbedder()
            self.vector_store = VectorStore(
                dimension=1024,  # qwen2.5-coder embedding dim
                index_path=self.knowledge_root / ".local_index"
            )
        else:
            self.embedder = None
            self.vector_store = None

    def build_index(self, rebuild: bool = False) -> int:
        """Build both BM25 and semantic indexes.

        Returns:
            Number of documents indexed
        """
        # Build BM25 index
        count = self.bm25.build_index()

        # Build semantic index if enabled
        if self.use_semantic and self.embedder:
            if self.embedder.check_connection():
                # Re-embed all documents
                embeddings = self.embedder.embed_batch([
                    f"{d['title']}: {d['content'][:1000]}"
                    for d in self.bm25.documents
                ])
                self.vector_store.add(embeddings, self.bm25.documents)
                self.vector_store.save()
            else:
                print("Warning: Ollama not available, using BM25 only")
                self.use_semantic = False

        return count

    def search(
        self,
        query: str,
        top_k: int = 10,
        use_hybrid: bool = True
    ) -> list[dict]:
        """Search using hybrid or single method.

        Args:
            query: Search query
            top_k: Number of results
            use_hybrid: Whether to use hybrid search

        Returns:
            List of results with combined scores
        """
        if not use_hybrid or not self.use_semantic:
            # BM25 only
            return self.bm25.search(query, top_k=top_k)

        # Get BM25 results
        bm25_results = self.bm25.search(query, top_k=top_k * 2)

        # Get semantic results
        query_embedding = self.embedder.embed(query)
        semantic_results = self.vector_store.search(query_embedding, top_k=top_k * 2)

        # Combine results
        return self._combine_results(bm25_results, semantic_results, top_k)

    def _combine_results(
        self,
        bm25_results: list[dict],
        semantic_results: list[dict],
        top_k: int
    ) -> list[dict]:
        """Combine BM25 and semantic results with reciprocal rank fusion."""
        # Build score maps
        bm25_scores = {r["file_path"]: r["score"] for r in bm25_results}
        semantic_scores = {r["file_path"]: 1 / (1 + r.get("distance", 1)) for r in semantic_results}

        # Get all unique files
        all_files = set(bm25_scores.keys()) | set(semantic_scores.keys())

        # Combine scores
        combined = []
        for file_path in all_files:
            bm25_score = bm25_scores.get(file_path, 0)
            semantic_score = semantic_scores.get(file_path, 0)

            # Normalize and combine
            combined_score = (
                self.bm25_weight * bm25_score +
                self.semantic_weight * semantic_score
            )

            # Find the document
            for r in bm25_results + semantic_results:
                if r["file_path"] == file_path:
                    doc = r.copy()
                    doc["combined_score"] = combined_score
                    doc["bm25_score"] = bm25_score
                    doc["semantic_score"] = semantic_score
                    combined.append(doc)
                    break

        # Sort by combined score
        combined.sort(key=lambda x: x["combined_score"], reverse=True)
        return combined[:top_k]
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat(retriever): add HybridSearch class

- Combine BM25 and semantic search
- Reciprocal rank fusion
- Configurable weights
"
```

---

## Module 4: 配置和脚本

### Task 4.1: 更新配置

**Files:**
- Modify: `config/settings.yaml`

- [ ] **Step 1: 添加本地检索配置**

```yaml
# Retriever settings (Phase 3)
retriever:
  # Cloud mode (requires Bailian embedding API)
  cloud:
    enabled: false  # Set to false to use local mode
    model: "text-embedding-v2"
    dimension: 1536

  # Local mode (BM25 + Ollama)
  local:
    enabled: true
    bm25_weight: 0.5
    semantic_weight: 0.5
    ollama_model: "qwen2.5-coder:7b"
    ollama_url: "http://localhost:11434"
    dimension: 1024

  index_path: "${PWD}/knowledge/index"
  top_k: 5
  min_score: 0.5
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "config: add local retriever settings

- BM25 + Ollama configuration
- Toggle between cloud and local mode
"
```

---

### Task 4.2: Ollama 安装脚本

**Files:**
- Create: `scripts/setup_ollama.sh`

- [ ] **Step 1: 创建安装脚本**

```bash
#!/bin/bash
# Setup Ollama for local retrieval

echo "=== Ollama Setup ==="

# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "Ollama is already installed"
else
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
fi

# Start Ollama service
echo "Starting Ollama service..."
ollama serve &
sleep 3

# Pull model
MODEL=${1:-"qwen2.5-coder:7b"}
echo "Pulling model: $MODEL"
ollama pull $MODEL

echo ""
echo "=== Setup Complete ==="
echo "Ollama is running at http://localhost:11434"
echo "Model: $MODEL"
echo ""
echo "Test with: ollama run $MODEL 'Hello'"
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "scripts: add setup_ollama.sh

- Install Ollama
- Pull qwen2.5-coder model
- Start service
"
```

---

### Task 4.3: 更新查询脚本

**Files:**
- Modify: `scripts/query.py`

- [ ] **Step 1: 添加本地模式支持**

```python
# Add --local flag
parser.add_argument("--local", action="store_true", help="Use local BM25+Ollama mode")
parser.add_argument("--hybrid", action="store_true", help="Use hybrid search")

# In main():
if args.local or args.hybrid:
    from src.retriever.hybrid_search import HybridSearch
    search = HybridSearch(
        knowledge_root=config.paths.get("knowledge_root", "./knowledge"),
        use_semantic=args.hybrid
    )
    results = search.search(args.query, top_k=args.top_k)
else:
    # Original cloud mode
    ...
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "scripts: update query.py with local mode support

- Add --local and --hybrid flags
- Support BM25 only or hybrid search
"
```

---

## Dependencies

### Task 4.4: 更新依赖

**Files:**
- Modify: `requirements.txt`

```txt
# Phase 3b: Local retrieval
rank-bm25>=0.2.2
jieba>=0.42.1
ollama>=0.1.7
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "chore: add local retrieval dependencies

- rank-bm25 for keyword search
- jieba for Chinese tokenization
- ollama for local embeddings
"
```

---

## Self-Review

### Spec Coverage

| Spec Requirement | Implementing Task |
|------------------|-------------------|
| BM25 关键词检索 | Task 1.1 |
| Ollama 本地嵌入 | Task 2.1 |
| 混合检索 | Task 3.1 |
| 配置文件 | Task 4.1 |
| Ollama 安装脚本 | Task 4.2 |
| 查询脚本更新 | Task 4.3 |
| 依赖更新 | Task 4.4 |

### Benefits vs Cloud

| Feature | Cloud (Bailian) | Local (BM25+Ollama) |
|---------|-----------------|---------------------|
| Cost | Per API call | Free (after setup) |
| Privacy | Data sent to cloud | 100% local |
| Speed | Fast (network) | Fast (local) |
| Quality | High | Good (7B model) |
| Setup | API key only | Ollama + model download |

---

## Execution

**Recommended approach:** Subagent-driven or inline?
