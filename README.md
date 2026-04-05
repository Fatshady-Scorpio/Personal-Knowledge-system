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

- **向量嵌入**: 使用阿里云百炼 text-embedding-v2
- **相似度搜索**: FAISS 高效索引
- **智能问答**: 基于检索结果生成答案
- **资料来源**: 自动引用来源
