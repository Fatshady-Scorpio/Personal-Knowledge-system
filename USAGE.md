# Personal Knowledge System 使用指南

## 快速开始

### 1. 环境准备

```bash
# 安装所有依赖
pip install -r requirements.txt

# 配置环境变量（如果还没配置）
cp .env.example .env
# 编辑 .env 添加你的阿里云百炼 API Key
```

### 2. 目录结构

```
personal-knowledge-system/
├── knowledge/              # 知识库根目录
│   ├── 00-Inbox/          # 新采集内容（待处理）
│   ├── 10-Raw/            # 原始内容
│   ├── 20-Processed/      # 处理后的内容（带摘要和标签）
│   ├── 30-Topics/         # 按主题组织
│   ├── 40-Maps/           # 知识图谱
│   └── 90-Archive/        # 归档
├── scripts/               # 命令行工具
├── src/                   # 源代码
└── tests/                 # 测试
```

---

## Phase 1: 手动采集 + 自动摘要

### 使用 Summarizer 处理文本

```python
from src.processor.summarizer import Summarizer

summarizer = Summarizer(output_dir="./knowledge/20-Processed")

# 处理文本并保存
result = summarizer.save_to_file(
    text="你的文章内容...",
    title="文章标题",
    source_url="https://example.com/article"
)

print(f"已保存到：{result}")
```

### 运行手动流程测试

```bash
python -m pytest tests/test_manual_flow.py -v
```

---

## Phase 2: 自动采集 + 知识图谱

### 网页爬取

```bash
# 爬取单个网页
python scripts/run_collector.py scrape --url "https://example.com/article"

# 输出会自动保存到 20-Processed 目录
```

### RSS 订阅

```bash
# 获取 RSS 条目
python scripts/run_collector.py rss --url "https://example.com/feed" --limit 10
```

### 配置数据源

编辑 `config/sources.yaml` 添加你的订阅源：

```yaml
domestic:
  rss_feeds:
    - name: "机器之心"
      url: "https://www.jiqizhixin.com/rss"
      category: "AI"
```

### 知识图谱

知识图谱自动在后台运行，当处理新内容时会自动建立关联。

```python
from src.graph.graph_store import GraphStore

graph = GraphStore(db_path="./knowledge/graph.db")

# 查看某个笔记的关联
related = graph.get_related("note-id")
for r in related:
    print(f"{r['title']} - {r['relation']}")
```

---

## Phase 3: 语义检索 + RAG 问答

### 方案 A: 本地检索（推荐，无需 API Key）

```bash
# 安装 Ollama 并下载模型
bash scripts/setup_ollama.sh

# 构建索引（BM25）
python scripts/query.py --local "测试查询"

# 使用混合检索（BM25 + 语义）
python scripts/query.py --hybrid "人工智能"
```

### 方案 B: 云端检索（需要 Embedding API Key）

```bash
# 首次构建索引（会处理 20-Processed 目录下的所有文件）
python scripts/build_index.py

# 重建索引
python scripts/build_index.py --rebuild
```

### 语义搜索

```bash
# 搜索相关内容（本地模式）
python scripts/query.py --local "人工智能的最新进展"

# 搜索相关内容（云端模式）
python scripts/query.py "人工智能的最新进展"

# 输出示例：
# 找到 5 个结果:
# [0.85] AI 大模型发展趋势
#     本文介绍了 2024 年 AI 大模型的发展趋势...
```

### RAG 问答

```bash
# 问答模式
python scripts/query.py --qa "什么是深度学习？"

# 输出示例：
# 答案：深度学习是机器学习的一个分支...
# 
# 资料来源:
#   - 机器学习基础 (score: 0.82)
#   - AI 模型介绍 (score: 0.75)
```

---

## Phase 4: Agent 深度集成

### 启动 API 服务

```bash
# 启动 FastAPI 服务器
python scripts/run_server.py --port 8000 --reload

# 访问 API 文档
# http://localhost:8000/docs
```

### API 端点

#### 搜索
```bash
curl -X GET "http://localhost:8000/api/v1/search?query=人工智能&top_k=5"
```

#### 问答
```bash
curl -X GET "http://localhost:8000/api/v1/qa?question=什么是机器学习&top_k=5"
```

#### 获取上下文（用于 Claude）
```bash
curl -X POST "http://localhost:8000/api/v1/context/get" \
  -H "Content-Type: application/json" \
  -d '{"query": "深度学习", "max_notes": 5, "session_id": "my_session"}'
```

#### 委托任务
```bash
# 委托爬取任务
curl -X POST "http://localhost:8000/api/v1/delegate/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/article", "save": true}'

# 委托研究任务
curl -X POST "http://localhost:8000/api/v1/delegate/research" \
  -H "Content-Type: application/json" \
  -d '{"topic": "人工智能的发展", "depth": 2}'
```

### Claude 上下文加载

```bash
# 获取主题上下文（输出可直接复制给 Claude）
python scripts/claude_context.py "机器学习"

# 保存上下文供后续使用
python scripts/claude_context.py "深度学习" --save --session dl

# 加载已保存的上下文
python scripts/claude_context.py --load --session dl
```

---

## 完整工作流示例

### 场景：跟踪 AI 领域最新动态

```bash
# 1. 采集 RSS 内容
python scripts/run_collector.py rss --url "https://www.jiqizhixin.com/rss" --limit 5

# 2. 采集特定网页
python scripts/run_collector.py scrape --url "https://example.com/ai-news"

# 3. 构建/更新索引
python scripts/build_index.py

# 4. 搜索相关内容
python scripts/query.py "大模型训练"

# 5. 如果有问题，使用问答模式
python scripts/query.py --qa "大模型训练的常见方法有哪些？"

# 6. 为 Claude 会话准备上下文
python scripts/claude_context.py "大模型训练" --save --session ai_research
```

---

## 常见问题

### 1. API Key 错误
确保 `.env` 文件中配置了正确的 API Key：
```
BAILOU_API_KEY=sk-xxxxx
```

### 2. 索引为空
确保 `20-Processed` 目录下有处理过的文件，然后运行：
```bash
python scripts/build_index.py --rebuild
```

### 3. 代理问题
如果使用代理，确保配置正确：
```bash
export http_proxy=http://your-proxy:port
export https_proxy=http://your-proxy:port
```

---

## 模型配置

编辑 `config/settings.yaml` 可以调整使用的模型：

```yaml
bailian:
  models:
    text_summary: "qwen3.5-plus"      # 文本摘要
    code_generation: "qwen3-coder-next"  # 代码生成
    long_text_analysis: "kimi-k2.5"   # 长文本
    complex_reasoning: "qwen3-max-2026-01-23"  # 复杂推理
```

---

## 测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定阶段测试
python -m pytest tests/test_phase1.py -v
python -m pytest tests/test_phase2_integration.py -v
python -m pytest tests/test_phase3_integration.py -v
python -m pytest tests/test_phase4_integration.py -v
```

---

## 下一步

目前系统已完成 Phase 1-4 的所有核心功能：
- ✅ 手动采集 + 自动摘要
- ✅ 自动采集 + 知识图谱
- ✅ 语义检索 + RAG 问答
- ✅ Agent 深度集成

后续可以根据需要：
1. 添加更多数据源
2. 优化向量索引性能
3. 扩展 Agent 集成能力
