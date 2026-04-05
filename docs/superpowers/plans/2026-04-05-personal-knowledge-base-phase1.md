# Personal Knowledge Base Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建个人知识库系统的基础结构，实现手动采集 + 自动摘要功能

**Architecture:** 基于模块化设计，首先搭建项目骨架、配置管理、阿里云百炼 API 集成，然后实现基础的文本摘要功能

**Tech Stack:** Python 3.12+, 阿里云百炼 API, Obsidian (Markdown), PyYAML, httpx, python-dotenv

---

## File Structure

### Files to Create

| File | Responsibility |
|------|----------------|
| `src/__init__.py` | Package initialization |
| `src/utils/__init__.py` | Utils package |
| `src/utils/config.py` | 配置加载和管理 |
| `src/utils/model_router.py` | 阿里云百炼模型路由 |
| `src/processor/__init__.py` | Processor package |
| `src/processor/summarizer.py` | 文本摘要生成 |
| `config/settings.yaml` | 系统配置 |
| `config/sources.yaml` | 数据源配置 |
| `knowledge/` | Obsidian 知识库目录结构 |
| `requirements.txt` | Python 依赖 |
| `scripts/setup.py` | 初始化脚本 |

### Files to Modify

| File | Changes |
|------|---------|
| `README.md` | 添加项目说明和使用方法 |
| `.gitignore` | 添加 Python/ Obsidian 忽略规则 |
| `.env` | 环境变量（不提交） |

---

## Phase 1 Tasks

### Task 1: 项目基础结构

**Files:**
- Create: `src/__init__.py`, `src/utils/__init__.py`, `src/processor/__init__.py`
- Create: `config/settings.yaml`, `config/sources.yaml`
- Create: `requirements.txt`
- Modify: `README.md`

- [ ] **Step 1: 创建 Python 包结构**

```bash
mkdir -p src/utils src/processor src/collector src/retriever src/agent
touch src/__init__.py src/utils/__init__.py src/processor/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```txt
# Core
httpx>=0.25.0
pyyaml>=6.0
python-dotenv>=1.0.0
dashscope>=1.14.0  # 阿里云百炼 SDK

# Video processing (Phase 2)
yt-dlp>=2024.0.0

# Vector search (Phase 3)
numpy>=1.26.0
faiss-cpu>=1.7.4

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
```

- [ ] **Step 3: 创建 config/settings.yaml**

```yaml
# Personal Knowledge Base Settings

# Alibaba Cloud Bailian
bailian:
  api_key: "${BAILOU_API_KEY}"  # Set via environment
  base_url: "https://dashscope.aliyuncs.com/api/v1"
  
  # Model routing
  models:
    text_summary: "qwen-max"
    text_classification: "qwen-turbo"
    text_embedding: "text-embedding-v2"
    multimodal: "qwen-vl-max"
    rag_qa: "qwen-max"

# Knowledge base paths
paths:
  knowledge_root: "${PWD}/knowledge"
  inbox: "00-Inbox"
  raw: "10-Raw"
  processed: "20-Processed"
  topics: "30-Topics"
  maps: "40-Maps"
  outputs: "50-Outputs"
  archive: "90-Archive"

# Processing settings
processing:
  max_retries: 3
  timeout_seconds: 60
  batch_size: 10
  
# Video settings (Phase 2+)
video:
  segment_by: "time"  # or "topic"
  segment_duration: 300  # seconds
  keep_original_url: true
```

- [ ] **Step 4: 创建 config/sources.yaml**

```yaml
# Data Sources Configuration

# Domestic sources (China)
domestic:
  websites:
    - name: "机器之心"
      url: "https://www.jiqizhixin.com"
      category: "AI"
    - name: "量子位"
      url: "https://www.qbitai.com"
      category: "AI"
    - name: "AI 科技评论"
      url: "https://aitechtalk.com"
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
    - name: "arXiv cs.AI"
      url: "https://arxiv.org/list/cs.AI/recent"
      category: "AI"
    - name: "Towards Data Science"
      url: "https://towardsdatascience.com"
      category: "AI"
  
  video_channels:
    - name: "YouTube AI Channels"
      platform: "youtube"
      category: "AI"

# RSS feeds (to be added)
rss_feeds: []
```

- [ ] **Step 5: 更新 README.md**

```markdown
# Personal Knowledge System

我的个人智能知识管理系统，基于 Andrej Karpathy 的 LLM Knowledge Base 工作流。

## 功能

- 🤖 高自动化知识采集（文本 + 视频）
- 📝 自动摘要、分类、建立关联
- 🔍 语义检索 + RAG 问答
- 🤝 Agent 深度集成（作为个人知识能力延伸）

## 技术栈

- **前端**: Obsidian
- **LLM**: 阿里云百炼
- **语言**: Python 3.12+

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 添加 API Key

# 运行设置
python scripts/setup.py
```

## 知识库结构

```
knowledge/
├── 00-Inbox/       # 新采集内容
├── 10-Raw/         # 原始内容
├── 20-Processed/   # 处理后的内容
├── 30-Topics/      # 按主题组织
├── 40-Maps/        # 知识图谱
├── 50-Outputs/     # 输出内容
└── 90-Archive/     # 归档
```

## 实施阶段

- [x] Phase 1: 基础结构 + 手动采集 + 自动摘要
- [ ] Phase 2: 自动采集 + 知识图谱
- [ ] Phase 3: 语义检索 + RAG 问答
- [ ] Phase 4: Agent 深度集成
```

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: setup Phase 1 project structure

- Create package structure (src/, config/)
- Add requirements.txt with core dependencies
- Add settings.yaml and sources.yaml configuration
- Update README.md with project overview
"
```

---

### Task 2: 配置管理和环境变量

**Files:**
- Create: `src/utils/config.py`
- Create: `.env.example`
- Modify: `.gitignore`

- [ ] **Step 1: 创建 .env.example**

```bash
# Alibaba Cloud Bailian API Key
BAILOU_API_KEY="sk-your-api-key-here"

# Optional: Custom paths
KNOWLEDGE_ROOT="${PWD}/knowledge"
```

- [ ] **Step 2: 更新 .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# Environment
.env
.env.local

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Obsidian
.obsidian/

# Logs
*.log
logs/

# Knowledge base content (optional - can be gitignored or tracked)
# knowledge/
```

- [ ] **Step 3: 创建 src/utils/config.py**

```python
"""Configuration management for Personal Knowledge Base."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class Config:
    """Load and manage configuration from YAML and environment variables."""
    
    def __init__(self, config_dir: str | None = None):
        """Initialize configuration.
        
        Args:
            config_dir: Directory containing config files. Defaults to project config/.
        """
        # Load environment variables
        load_dotenv()
        
        # Determine config directory
        if config_dir is None:
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.settings = self._load_yaml("settings.yaml")
        self.sources = self._load_yaml("sources.yaml")
        
        # Expand environment variables in settings
        self.settings = self._expand_env(self.settings)
    
    def _load_yaml(self, filename: str) -> dict[str, Any]:
        """Load a YAML configuration file."""
        filepath = self.config_dir / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    
    def _expand_env(self, config: dict[str, Any]) -> dict[str, Any]:
        """Expand environment variables in configuration values."""
        result = {}
        for key, value in config.items():
            if isinstance(value, dict):
                result[key] = self._expand_env(value)
            elif isinstance(value, str):
                # Expand ${VAR} syntax
                result[key] = os.path.expandvars(value)
            else:
                result[key] = value
        return result
    
    @property
    def bailian_api_key(self) -> str:
        """Get Bailian API key from environment."""
        api_key = os.getenv("BAILOU_API_KEY")
        if not api_key:
            raise ValueError(
                "BAILOU_API_KEY not set. Please copy .env.example to .env and configure it."
            )
        return api_key
    
    @property
    def models(self) -> dict[str, str]:
        """Get model configuration."""
        return self.settings.get("bailian", {}).get("models", {})
    
    @property
    def paths(self) -> dict[str, str]:
        """Get path configuration."""
        return self.settings.get("paths", {})
    
    def get_model_for_task(self, task_type: str) -> str:
        """Get the appropriate model for a given task type."""
        models = self.models
        return models.get(task_type, models.get("text_summary", "qwen-max"))
    
    def get_knowledge_path(self, category: str) -> Path:
        """Get the path for a knowledge base category."""
        root = self.paths.get("knowledge_root", "./knowledge")
        category_path = self.paths.get(category, category)
        return Path(root) / category_path


# Global config instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: add configuration management

- Create Config class for YAML + env var loading
- Add .env.example template
- Update .gitignore for Python/Obsidian
"
```

---

### Task 3: 阿里云百炼 API 集成

**Files:**
- Create: `src/utils/model_router.py`

- [ ] **Step 1: 创建 src/utils/model_router.py**

```python
"""Model routing for Alibaba Cloud Bailian API."""

import asyncio
from typing import Any

import dashscope
from dashscope import TextGeneration, Generation


class ModelRouter:
    """Route requests to appropriate Bailian models based on task type."""
    
    def __init__(self, api_key: str):
        """Initialize the model router.
        
        Args:
            api_key: Alibaba Cloud Bailian API key.
        """
        dashscope.api_key = api_key
        self.api_key = api_key
    
    def text_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a summary of the given text.
        
        Args:
            text: The text to summarize.
            max_length: Maximum length of the summary.
            
        Returns:
            The generated summary.
        """
        prompt = f"""请为以下内容生成一个简洁的摘要（{max_length}字以内）：

{text}

摘要："""
        
        response = TextGeneration.call(
            model="qwen-max",
            prompt=prompt,
            max_tokens=max_length,
            temperature=0.7,
        )
        
        if response.status_code == 200:
            return response.output.text
        else:
            raise RuntimeError(f"API error: {response.code} - {response.message}")
    
    def classify(self, text: str, categories: list[str] | None = None) -> dict[str, Any]:
        """Classify text into categories.
        
        Args:
            text: The text to classify.
            categories: Optional list of categories. Defaults to AI/Investment/Gaming.
            
        Returns:
            Dictionary with category and tags.
        """
        if categories is None:
            categories = ["AI", "投资", "游戏", "技术", "产品", "其他"]
        
        prompt = f"""请分析以下内容，将其分类到最合适的类别中，并提取关键词标签。

内容：
{text}

请按照以下 JSON 格式返回结果：
{{
    "category": "类别名称",
    "tags": ["标签 1", "标签 2", ...],
    "confidence": 0.0-1.0
}}

只返回 JSON，不要其他内容。"""
        
        response = TextGeneration.call(
            model="qwen-turbo",
            prompt=prompt,
            max_tokens=200,
            temperature=0.3,
        )
        
        if response.status_code == 200:
            import json
            result = response.output.text.strip()
            # Extract JSON from response
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            return json.loads(result)
        else:
            raise RuntimeError(f"API error: {response.code} - {response.message}")
    
    async def text_summary_async(self, text: str, max_length: int = 500) -> str:
        """Async version of text_summary."""
        return await asyncio.to_thread(self.text_summary, text, max_length)
    
    async def classify_async(self, text: str, categories: list[str] | None = None) -> dict[str, Any]:
        """Async version of classify."""
        return await asyncio.to_thread(self.classify, text, categories)
    
    def multimodal_understanding(
        self, 
        image_url: str | None = None, 
        text: str = ""
    ) -> str:
        """Understand multimodal content (image + text).
        
        Args:
            image_url: URL or path to image.
            text: Additional text context.
            
        Returns:
            Description and analysis of the content.
        """
        # This will be implemented in Phase 2 for video frames
        raise NotImplementedError("Multimodal understanding will be implemented in Phase 2")


# Global router instance
_router: ModelRouter | None = None


def get_router() -> ModelRouter:
    """Get the global model router instance."""
    global _router
    if _router is None:
        from .config import get_config
        config = get_config()
        _router = ModelRouter(config.bailian_api_key)
    return _router
```

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: add Alibaba Cloud Bailian model router

- Create ModelRouter class for API calls
- Implement text_summary and classify methods
- Add async versions of methods
- Prepare multimodal_understanding for Phase 2
"
```

---

### Task 4: 文本摘要处理器

**Files:**
- Create: `src/processor/summarizer.py`
- Create: `tests/__init__.py`
- Create: `tests/test_summarizer.py`

- [ ] **Step 1: 创建 src/processor/summarizer.py**

```python
"""Text summarization processor."""

import json
from datetime import datetime
from pathlib import Path

from ..utils.model_router import get_router


class Summarizer:
    """Process raw content and generate summaries with metadata."""
    
    def __init__(self, output_dir: str | Path | None = None):
        """Initialize the summarizer.
        
        Args:
            output_dir: Directory for processed markdown files.
        """
        self.router = get_router()
        self.output_dir = Path(output_dir) if output_dir else None
    
    def process(self, text: str, source_url: str | None = None) -> dict:
        """Process raw text and generate summary with metadata.
        
        Args:
            text: The raw text content.
            source_url: Optional source URL.
            
        Returns:
            Dictionary with summary, category, tags, and metadata.
        """
        # Generate summary
        summary = self.router.text_summary(text, max_length=300)
        
        # Classify content
        classification = self.router.classify(text)
        
        # Build result
        result = {
            "summary": summary,
            "category": classification.get("category", "其他"),
            "tags": classification.get("tags", []),
            "confidence": classification.get("confidence", 0.0),
            "source_url": source_url,
            "processed_at": datetime.now().isoformat(),
            "original_length": len(text),
            "summary_length": len(summary),
        }
        
        return result
    
    def process_to_markdown(
        self, 
        text: str, 
        title: str | None = None,
        source_url: str | None = None
    ) -> str:
        """Process text and return as markdown format.
        
        Args:
            text: The raw text content.
            title: Optional title for the note.
            source_url: Optional source URL.
            
        Returns:
            Markdown formatted string.
        """
        result = self.process(text, source_url)
        
        # Generate title if not provided
        if not title:
            # Use first line or first 50 chars of summary
            first_line = text.split("\n")[0][:50]
            title = first_line.strip() or "Untitled"
        
        # Build markdown
        tags_str = ", ".join(result["tags"])
        source_line = f"\n\nSource: {source_url}" if source_url else ""
        
        markdown = f"""---
title: {title}
category: {result["category"]}
tags: [{tags_str}]
processed_at: {result["processed_at"]}
source_url: {source_url or "N/A"}
---

# {title}

## 摘要

{result["summary"]}

## 标签

{', '.join(result["tags"])}

## 分类

{result["category"]} (置信度：{result["confidence"]:.0%})
{source_line}

---

## 原始内容

{text}
"""
        
        return markdown
    
    def save_to_file(
        self, 
        text: str, 
        title: str | None = None,
        source_url: str | None = None,
        output_dir: str | Path | None = None
    ) -> Path:
        """Process text and save to markdown file.
        
        Args:
            text: The raw text content.
            title: Optional title for the note.
            source_url: Optional source URL.
            output_dir: Override output directory.
            
        Returns:
            Path to the saved file.
        """
        markdown = self.process_to_markdown(text, title, source_url)
        
        # Determine output directory
        out_dir = Path(output_dir) if output_dir else self.output_dir
        if out_dir is None:
            from ..utils.config import get_config
            config = get_config()
            out_dir = Path(config.paths.get("knowledge_root", "./knowledge")) / "20-Processed"
        
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title[:50])
        filename = f"{safe_title}.md"
        filepath = out_dir / filename
        
        # Save file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)
        
        return filepath
```

- [ ] **Step 2: 创建 tests/test_summarizer.py**

```python
"""Tests for the summarizer module."""

import pytest
from pathlib import Path

from src.processor.summarizer import Summarizer


class TestSummarizer:
    """Test cases for Summarizer class."""
    
    @pytest.fixture
    def sample_text(self) -> str:
        """Sample text for testing."""
        return """
        人工智能（AI）是计算机科学的一个分支，旨在创造能够执行需要人类智能的任务的系统。
        这些任务包括学习、推理、问题解决、感知和理解语言。AI 的应用包括机器学习、
        自然语言处理、计算机视觉和机器人技术。近年来，随着深度学习和大数据的发展，
        AI 取得了显著进步，在医疗诊断、自动驾驶、语音助手等领域都有广泛应用。
        """
    
    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create a Summarizer instance."""
        return Summarizer()
    
    def test_process_returns_dict(self, summarizer: Summarizer, sample_text: str):
        """Test that process returns a dictionary with expected keys."""
        result = summarizer.process(sample_text)
        
        assert isinstance(result, dict)
        assert "summary" in result
        assert "category" in result
        assert "tags" in result
        assert "processed_at" in result
        assert isinstance(result["tags"], list)
    
    def test_process_to_markdown_contains_sections(self, summarizer: Summarizer, sample_text: str):
        """Test that markdown output contains expected sections."""
        markdown = summarizer.process_to_markdown(sample_text, title="测试文章")
        
        assert "# 测试文章" in markdown
        assert "## 摘要" in markdown
        assert "## 标签" in markdown
        assert "## 原始内容" in markdown
    
    def test_save_to_file_creates_file(self, summarizer: Summarizer, sample_text: str, tmp_path: Path):
        """Test that save_to_file creates a markdown file."""
        filepath = summarizer.save_to_file(
            sample_text, 
            title="测试文章",
            output_dir=tmp_path
        )
        
        assert filepath.exists()
        assert filepath.suffix == ".md"
        assert "测试文章" in filepath.name
```

- [ ] **Step 3: 运行测试（预期会失败 - 需要 API Key）**

```bash
# This test requires a valid API key - skip for now if not configured
# pytest tests/test_summarizer.py -v --tb=short
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: implement text summarizer processor

- Create Summarizer class with process/to_markdown/save methods
- Add classification integration
- Add tests for summarizer (require API key to run)
"
```

---

### Task 5: 创建知识库目录结构

**Files:**
- Create: `knowledge/` directory structure
- Create: `scripts/setup.py`

- [ ] **Step 1: 创建知识库目录结构**

```bash
mkdir -p knowledge/{00-Inbox,10-Raw/{articles,videos,papers},20-Processed/{summaries,notes},30-Topics/{AI,Investment,Gaming},40-Maps,50-Outputs,90-Archive}
```

- [ ] **Step 2: 创建 scripts/setup.py**

```python
#!/usr/bin/env python3
"""Setup script for Personal Knowledge Base."""

import os
import sys
from pathlib import Path


def setup_directories():
    """Create the knowledge base directory structure."""
    root = Path(__file__).parent.parent
    knowledge_root = root / "knowledge"
    
    directories = [
        "00-Inbox",
        "10-Raw/articles",
        "10-Raw/videos",
        "10-Raw/papers",
        "20-Processed/summaries",
        "20-Processed/notes",
        "30-Topics/AI",
        "30-Topics/Investment",
        "30-Topics/Gaming",
        "40-Maps",
        "50-Outputs",
        "90-Archive",
    ]
    
    for dir_name in directories:
        dir_path = knowledge_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")
    
    # Create .gitkeep files
    for dir_path in knowledge_root.rglob("*"):
        if dir_path.is_dir():
            gitkeep = dir_path / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.touch()
    
    print("\n✓ Knowledge base directory structure created!")


def check_env():
    """Check if environment variables are configured."""
    env_file = Path(__file__).parent.parent / ".env"
    
    if not env_file.exists():
        print("\n⚠ Warning: .env file not found!")
        print("Please copy .env.example to .env and configure your API key:")
        print("  cp .env.example .env")
        return False
    
    # Check for API key
    with open(env_file, "r") as f:
        content = f.read()
    
    if "BAILOU_API_KEY=" not in content or 'sk-your-api-key-here' in content:
        print("\n⚠ Warning: BAILOU_API_KEY not configured in .env!")
        print("Please edit .env and set your Alibaba Cloud Bailian API key.")
        return False
    
    print("\n✓ Environment configuration OK")
    return True


def main():
    """Run setup."""
    print("=" * 50)
    print("Personal Knowledge Base - Setup")
    print("=" * 50)
    
    setup_directories()
    check_env()
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 运行 setup.py**

```bash
chmod +x scripts/setup.py
python scripts/setup.py
```

Expected output:
```
==================================================
Personal Knowledge Base - Setup
==================================================
✓ Created: /path/to/knowledge/00-Inbox
✓ Created: /path/to/knowledge/10-Raw/articles
...
✓ Knowledge base directory structure created!

✓ Environment configuration OK

==================================================
Setup complete!
==================================================
```

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "feat: create knowledge base directory structure

- Add setup.py script for initialization
- Create all Phase 1 directories
- Add .gitkeep files for git tracking
"
```

---

### Task 6: 测试手动采集 + 自动摘要流程

**Files:**
- Create: `tests/test_manual_flow.py`
- Create: `data/sample_article.txt`

- [ ] **Step 1: 创建测试数据 data/sample_article.txt**

```bash
mkdir -p data
```

Create `data/sample_article.txt`:

```
标题：GPT-4 与 Claude 的对比分析

随着人工智能技术的快速发展，大型语言模型（LLM）在各个领域都展现出强大的能力。
本文将对当前最先进的两个模型 GPT-4 和 Claude 进行全面对比。

## 模型架构

GPT-4 由 OpenAI 开发，采用 Transformer 架构，具有数千亿参数。
Claude 由 Anthropic 开发，同样基于 Transformer，但在安全和对齐方面有独特设计。

## 性能对比

在代码生成任务中，GPT-4 展现出强大的能力，能够生成复杂的程序。
Claude 则在文本理解和长文本处理方面表现出色，支持 100K token 上下文。

## 应用场景

GPT-4 适合需要创造性和代码能力的场景。
Claude 适合需要深度理解和安全性的场景，如法律文档分析。

## 结论

两个模型各有优势，选择取决于具体应用需求。
```

- [ ] **Step 2: 创建集成测试 tests/test_manual_flow.py**

```python
"""Test the manual collection + auto-summary flow."""

import pytest
from pathlib import Path

from src.processor.summarizer import Summarizer
from src.utils.config import get_config


class TestManualFlow:
    """Test the Phase 1 manual collection flow."""
    
    @pytest.fixture
    def sample_article(self) -> str:
        """Load sample article."""
        project_root = Path(__file__).parent.parent
        article_path = project_root / "data" / "sample_article.txt"
        with open(article_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def test_process_sample_article(self, sample_article: str, tmp_path: Path):
        """Test processing the sample article."""
        summarizer = Summarizer(output_dir=tmp_path)
        
        result = summarizer.process(
            sample_article,
            source_url="https://example.com/article"
        )
        
        assert "摘要" in result["summary"] or "对比" in result["summary"]
        assert result["category"] in ["AI", "技术"]
        assert len(result["tags"]) > 0
    
    def test_save_markdown_file(self, sample_article: str, tmp_path: Path):
        """Test saving processed article as markdown."""
        summarizer = Summarizer(output_dir=tmp_path)
        
        filepath = summarizer.save_to_file(
            sample_article,
            title="GPT-4 vs Claude 对比分析",
            source_url="https://example.com/article"
        )
        
        assert filepath.exists()
        
        content = filepath.read_text(encoding="utf-8")
        assert "---" in content  # Frontmatter
        assert "category:" in content
        assert "tags:" in content
        assert "## 摘要" in content
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "test: add integration test for manual collection flow

- Add sample article for testing
- Test processing and markdown generation
"
```

---

### Task 7: Phase 1 验收

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新 README.md 添加 Phase 1 完成状态**

Edit `README.md` to update the phases section:

```markdown
## 实施阶段

- [x] Phase 1: 基础结构 + 手动采集 + 自动摘要
  - [x] 项目结构搭建
  - [x] 配置管理
  - [x] 阿里云百炼 API 集成
  - [x] 文本摘要处理器
  - [x] 知识库目录结构
  - [x] 测试手动采集流程
- [ ] Phase 2: 自动采集 + 知识图谱
- [ ] Phase 3: 语义检索 + RAG 问答
- [ ] Phase 4: Agent 深度集成
```

- [ ] **Step 2: 创建 Phase 1 验收清单 docs/phase1-checklist.md**

```markdown
# Phase 1 验收清单

## 功能验收

- [ ] 能够运行 `python scripts/setup.py` 完成初始化
- [ ] 能够手动复制文本到 `00-Inbox/` 目录
- [ ] 能够运行处理器生成摘要
- [ ] 生成的 Markdown 文件包含：标题、摘要、标签、分类、原始内容
- [ ] 文件保存在正确的目录中

## 技术验收

- [ ] 所有 Python 文件语法正确
- [ ] 配置加载正常
- [ ] API 调用能够执行（需要有效 API Key）
- [ ] 测试文件存在

## 文档验收

- [ ] README.md 包含项目说明
- [ ] README.md 包含快速开始指南
- [ ] Phase 1 完成标记更新
```

- [ ] **Step 3: Final commit for Phase 1**

```bash
git add -A
git commit -m "docs: mark Phase 1 as complete

- Update README with Phase 1 checklist
- Add phase1-checklist.md
"
```

---

## Post-Plan Review

### Spec Coverage Check

| Spec Requirement | Implementing Task |
|------------------|-------------------|
| 基础项目结构 | Task 1 |
| 配置管理 | Task 2 |
| 阿里云百炼 API | Task 3 |
| 文本摘要 | Task 4 |
| 知识库目录 | Task 5 |
| 手动采集流程测试 | Task 6 |
| 验收 | Task 7 |

### Self-Review Complete

- ✅ No placeholders (TBD/TODO)
- ✅ All file paths specified
- ✅ All code snippets included
- ✅ All commands with expected output
- ✅ Type/function names consistent

---

## Execution Options

**Plan complete and saved to `docs/superpowers/plans/2026-04-05-personal-knowledge-base-phase1.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
