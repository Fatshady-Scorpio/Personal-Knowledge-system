# Personal Knowledge Base System Design

**Created**: 2026-04-05  
**Author**: Personal Knowledge System Team  
**Status**: Draft → Review → Approved

---

## 1. Overview

### 1.1 Purpose

构建一个高度自动化的个人智能知识库系统，基于 Andrej Karpathy 的 LLM Knowledge Base 工作流，使用 Obsidian 作为前端，阿里云百炼作为 LLM 服务，实现知识的自动采集、整理、摘要、关联和检索。

### 1.2 User Profile

- **角色**: 互联网产品经理
- **关注领域**: AI 技术、投资、游戏等多元领域
- **内容类型**: 文本（文章、论文）、视频（YouTube、课程）
- **数据来源**: 国内外双语内容

### 1.3 Core Requirements

1. **海量知识采集** - 多模态内容（文本 + 视频），自动采集
2. **高自动化整理** - 自动分类、摘要、建立关联
3. **强大检索能力** - 语义检索 + RAG 问答
4. **Agent 深度集成** - 作为个人知识能力延伸（Level D）

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │  Obsidian   │  │   Web UI     │  │    Claude/Agent API     │ │
│  │  (Primary)  │  │  (Optional)  │  │  (Knowledge Extension)  │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Services                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │  Collector  │  │  Processor   │  │    Retriever Service    │ │
│  │  Service    │  │   Service    │  │                         │ │
│  │ - Scraper   │  │ - Summarize  │  │  - Embedding            │ │
│  │ - RSS       │  │ - Classify   │  │  - Semantic Search      │ │
│  │ - Video     │  │ - Link Build │  │  - RAG Q&A              │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Model Routing Layer                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Alibaba Cloud Bailian API                       ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  ││
│  │  │ Multimodal   │  │ Text Model   │  │  Code/Other      │  ││
│  │  │ (Video)      │  │ (Summary)    │  │                  │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Storage Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │  Markdown   │  │   Vector     │  │    Metadata             │ │
│  │  (Obsidian) │  │   Database   │  │    (SQLite/JSON)        │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Module Design

### 3.1 Collector Service

**职责**: 从多源采集内容，支持去重和更新检测

#### Components

| Component | Responsibility |
|-----------|----------------|
| `web_scraper.py` | 网页爬取，支持国内外网站 |
| `rss_fetcher.py` | RSS 订阅源定时抓取 |
| `video_processor.py` | 视频下载、分段、字幕提取 |

#### Video Processing Flow

```
Video URL → Download Metadata → Extract Subtitles → 
Segment by Topic/Time → Call Multimodal API → 
Generate Segment Summary → Store with Original URL
```

### 3.2 Processor Service

**职责**: LLM 自动处理采集内容

#### Components

| Component | Responsibility |
|-----------|----------------|
| `summarizer.py` | 生成内容摘要 |
| `classifier.py` | 自动分类（AI/投资/游戏等） |
| `link_builder.py` | 分析关联，建立双向链接 |

#### Processing Pipeline

```
Raw Content → LLM Analysis → 
{Summary, Tags, Categories, Related Notes} → 
Processed Markdown → Obsidian Vault
```

### 3.3 Retriever Service

**职责**: 提供语义检索和 RAG 问答能力

#### Components

| Component | Responsibility |
|-----------|----------------|
| `embedder.py` | 生成向量嵌入 |
| `semantic_search.py` | 相似度搜索 |
| `rag_qa.py` | 基于知识库的智能问答 |

### 3.4 Agent Integration

**职责**: 与 Claude/外部 Agent 深度集成

#### Components

| Component | Responsibility |
|-----------|----------------|
| `knowledge_api.py` | 知识 API 供外部调用 |
| `context_injector.py` | Claude 会话自动加载上下文 |

#### Integration Levels (D - Full)

- 知识库作为 Agent 的"长期记忆"
- 支持复杂任务委托
- Agent 之间共享知识状态

---

## 4. Directory Structure

```
personal-knowledge-system/
├── README.md
├── docs/
│   └── superpowers/specs/
│       └── 2026-04-05-personal-knowledge-base-design.md
├── src/
│   ├── __init__.py
│   ├── collector/
│   │   ├── __init__.py
│   │   ├── web_scraper.py
│   │   ├── rss_fetcher.py
│   │   └── video_processor.py
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── summarizer.py
│   │   ├── classifier.py
│   │   └── link_builder.py
│   ├── retriever/
│   │   ├── __init__.py
│   │   ├── embedder.py
│   │   ├── semantic_search.py
│   │   └── rag_qa.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── knowledge_api.py
│   │   └── context_injector.py
│   └── utils/
│       ├── __init__.py
│       ├── model_router.py
│       └── config.py
├── config/
│   ├── settings.yaml
│   └── sources.yaml
├── knowledge/
│   ├── 00-Inbox/
│   ├── 10-Raw/
│   ├── 20-Processed/
│   ├── 30-Topics/
│   │   ├── AI/
│   │   ├── Investment/
│   │   ├── Gaming/
│   │   └── ...
│   ├── 40-Maps/
│   ├── 50-Outputs/
│   └── 90-Archive/
├── tests/
├── requirements.txt
└── scripts/
    ├── run_collector.py
    ├── run_processor.py
    └── run_server.py
```

---

## 5. Knowledge Base Structure

```
knowledge/
├── 00-Inbox/           # 新采集内容（待处理）
├── 10-Raw/             # 原始内容归档
│   ├── articles/
│   ├── videos/
│   └── papers/
├── 20-Processed/       # LLM 处理后的内容
│   ├── summaries/
│   └── notes/
├── 30-Topics/          # 按主题组织
│   ├── AI/
│   ├── Investment/
│   ├── Gaming/
│   └── ...
├── 40-Maps/            # 知识图谱/MOCs
├── 50-Outputs/         # 输出内容（文章、报告）
└── 90-Archive/         # 归档内容
```

---

## 6. Configuration

### 6.1 Model Routing (Alibaba Cloud Bailian)

| Task Type | Model | Reason |
|-----------|-------|--------|
| Video Understanding | Multimodal (Qwen-VL) | 支持图像 + 文本输入 |
| Text Summary | Qwen-Max/Plus | 高质量文本处理 |
| Classification | Qwen-Turbo | 低成本，快速 |
| Embedding | Text Embedding V2 | 语义向量 |
| RAG Q&A | Qwen-Max | 高质量回答 |

### 6.2 Data Sources (Initial)

**国内源**:
- 机器之心、量子位、AI 科技评论
- 知乎 AI 话题
- 哔哩哔哩技术 UP 主

**国外源**:
- Hacker News
- Twitter/X (AI researchers)
- YouTube (AI channels)
- arXiv (cs.AI, cs.LG)
- Medium (Towards Data Science)

---

## 7. Implementation Phases

| Phase | Content | Estimated Time |
|-------|---------|----------------|
| **Phase 1** | 基础结构 + 手动采集 + 自动摘要 | 1-2 天 |
| **Phase 2** | 自动采集 + 知识图谱 | 3-5 天 |
| **Phase 3** | 语义检索 + RAG 问答 | 5-7 天 |
| **Phase 4** | Agent 深度集成 | 7-10 天 |

---

## 8. Success Criteria

- [ ] Obsidian 中可见自动采集的内容
- [ ] 每条内容有 LLM 生成的摘要和标签
- [ ] 内容间有自动建立的双向链接
- [ ] 可以通过语义搜索找到相关内容
- [ ] 可以通过自然语言问答获取知识库信息
- [ ] Claude 可以读取知识库上下文辅助回答

---

## 9. Notes

- 所有 API 调用通过阿里云百炼，使用已配置的 API Key
- 视频处理保留原地址链接，便于回看
- 支持用户手动补充和完善采集源
- 知识库结构可持续迭代完善
