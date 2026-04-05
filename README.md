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
  - [x] 项目结构搭建
  - [x] 配置管理
  - [x] 阿里云百炼 API 集成
  - [x] 文本摘要处理器
  - [x] 知识库目录结构
  - [x] 测试手动采集流程
- [x] Phase 2: 自动采集 + 知识图谱
  - [x] 网页爬虫模块
  - [x] RSS 订阅模块
  - [x] 知识图谱存储
  - [x] 链接分析器
  - [x] 采集服务脚本
  - [x] 集成测试
- [x] Phase 3: 语义检索 + RAG 问答
  - [x] 向量嵌入生成器
  - [x] FAISS 向量存储
  - [x] 语义搜索
  - [x] RAG 问答
  - [x] 命令行工具
  - [x] 集成测试
- [x] Phase 4: Agent 深度集成
  - [x] 知识 API 服务
  - [x] 上下文注入器
  - [x] 任务委托模块
  - [x] FastAPI 服务器
  - [x] Claude 上下文加载
  - [x] 集成测试
- [x] Phase 5: 自动化系统
  - [x] 定时任务调度器
  - [x] 每日简报生成器
  - [x] 优先级过滤器
  - [x] 用户兴趣配置
  - [x] 预配置内容源

## Phase 5: 自动化系统（新增）

### 启动自动调度器

```bash
# 首次运行（手动触发一次）
python scripts/start_scheduler.py --run-once

# 启动后台调度服务
python scripts/start_scheduler.py

# macOS 开机自启
cp deploy/com.personal.kb.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.personal.kb.plist
```

### 配置文件

- `config/schedule.yaml` - 定时任务配置
- `config/user_interests.yaml` - 你的兴趣关键词
- `config/sources.yaml` - RSS 订阅源

### 每日简报

系统每天 9:00 自动生成简报，保存在：
```
knowledge/50-Outputs/daily_briefing_YYYY-MM-DD.md
```

### 优先级过滤

系统自动过滤低优先级内容，只处理你感兴趣的文章：
- 高优先级源（机器之心、arXiv 等）自动处理
- 包含兴趣关键词（LLM、RAG 等）的文章优先
- 自动忽略广告、推广内容

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

## Phase 3 功能

### 语义搜索（本地混合检索）

```bash
# 安装 Ollama（首次使用）
bash scripts/setup_ollama.sh

# 搜索内容（默认混合检索：BM25 0.7 + 语义 0.3）
python scripts/query.py "人工智能的最新进展"

# 仅使用 BM25
python scripts/query.py "人工智能" --bm25-only

# 调整权重
python scripts/query.py "人工智能" --bm25-weight 0.5 --semantic-weight 0.5
```

### RAG 问答

```bash
# 问答模式（使用本地检索 + 云端 LLM）
python scripts/query.py --qa "什么是深度学习？"
```

### 功能特点

- **混合检索**: BM25 关键词匹配 (70%) + Ollama 语义相似度 (30%)
- **完全本地**: 向量生成使用本地 Ollama，无需云端 API
- **可调权重**: 根据实际效果调整 BM25/语义比例
- **智能排序**: 综合两种检索方式的优势

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
