# Personal Knowledge System - Agentic Wiki 架构

> **快速上手**: 阅读 [docs/AGENTIC_WIKI_GUIDE.md](./docs/AGENTIC_WIKI_GUIDE.md)

## 项目概述

Personal Knowledge System 是一个基于 **Agentic Wiki 架构** 的个人知识管理系统，基于 Andrej Karpathy 提出的"LLM Wiki"范式。

### 核心理念

**手动输入 + LLM 编译 = 有状态的知识生长**：

| 维度 | 设计 |
|------|------|
| 内容来源 | 手动输入（文章、笔记、英文内容） |
| 处理时机 | 手动触发编译 |
| 存储格式 | 结构化 wiki + 双向链接 |
| 导航方式 | index.md + 图遍历 |
| 查询机制 | 有状态 wiki 导航 |
| 知识积累 | 网状复利 |

### 核心工作流

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌─────────────┐
│  手动输入   │ ──► │  LLM 编译     │ ──► │  深度查询   │ ──► │  健康检查   │
│  Raw 材料    │     │  Wiki 词条    │     │  知识复利   │     │  维护清理   │
└─────────────┘     └──────────────┘     └─────────────┘     └─────────────┘
```

---

## 目录结构

```
Personal Knowledge system/
├── raw/                    # 原始材料（手动输入，不可变）
│   ├── articles/           # 文章/博客/论文
│   └── notes/              # 临时想法/笔记
│
├── wiki/                   # 结构化知识（LLM 编译，持续生长）
│   ├── index.md            # 核心：内容导向的导航目录
│   ├── concepts/           # 概念词条（双向链接节点）
│   └── topics/             # 主题 MOC（Map of Content）
│
├── outputs/                # 高价值产出
│   └── qa/                 # 问答记录
│
├── src/
│   ├── compiler/           # LLM 编译器（核心）
│   │   ├── raw_processor.py      # Raw 材料读写/状态管理
│   │   ├── wiki_builder.py       # LLM 编译 Raw → Wiki（含英译中）
│   │   ├── link_extractor.py     # 双向链接提取/验证
│   │   └── index_generator.py    # index.md 生成/增量更新
│   ├── query/              # 深度查询引擎
│   │   ├── agent_query.py        # 有状态 Wiki 问答
│   │   └── context_manager.py    # Token 预算管理
│   ├── maintenance/        # 健康检查
│   │   └── health_checker.py     # 链接/矛盾/过期检测
│   ├── server/
│   │   └── wiki_chat_api.py      # FastAPI Chat API
│   └── utils/
│       ├── config.py             # 配置管理
│       └── model_router.py       # 多模型路由
│
├── config/
│   ├── wiki_config.yaml    # Wiki 配置
│   └── user_profile.yaml   # 用户偏好
│
└── scripts/
    ├── compile_raw.py          # 编译 Raw → Wiki
    ├── query_wiki.py           # 深度查询
    ├── chat.py                 # 交互式聊天
    ├── health_check.py         # 健康检查
    ├── start_chat_api.py       # 启动 Chat API
    ├── pdf_to_md.py            # PDF 转 Markdown
    └── translate_agentic_book.py  # 英译中工具
```

---

## 快速开始

### 1. 保存 Raw 材料

**方式 A：手动创建 Raw 材料**

将你想处理的内容保存为 markdown 文件到 `raw/articles/` 目录：

```markdown
---
type: article
source: https://example.com/article
collected_at: 2026-04-07
tags: [LLM, AI]
status: raw
---

# 文章标题

[文章内容或摘要]

---

## 我的思考

[你手写的思考/笔记]
```

**方式 B：PDF 文档转换**

```bash
# 转换 PDF 为可编译的 Markdown
PYTHONPATH=. python scripts/pdf_to_md.py /path/to/document.pdf

# 指定输出目录
PYTHONPATH=. python scripts/pdf_to_md.py --output raw/articles /path/to/document.pdf
```

### 2. 编译为 Wiki 词条

```bash
# 编译所有待处理的 Raw 材料
PYTHONPATH=. python scripts/compile_raw.py --all

# 或编译单个文件
PYTHONPATH=. python scripts/compile_raw.py --file raw/articles/20260407_文章标题.md
```

### 3. 查询知识库

**交互式聊天（推荐）**
```bash
PYTHONPATH=. python scripts/chat.py
```

**命令行查询**
```bash
# 直接查询
PYTHONPATH=. python scripts/query_wiki.py "什么是 Transformer？"

# 交互式查询
PYTHONPATH=. python scripts/query_wiki.py --interactive
```

### 4. 健康检查

```bash
PYTHONPATH=. python scripts/health_check.py --verbose
```

---

## 核心模块说明

### src/compiler/

#### RawProcessor
处理 Raw 材料的读取、创建和状态管理。

```python
from src.compiler.raw_processor import RawProcessor

processor = RawProcessor(raw_dir=Path("./raw"))

# 读取 Raw 材料
material = processor.read(Path("raw/articles/20260407_文章.md"))

# 创建新的 Raw 材料
path = processor.create(
    title="文章标题",
    content="内容摘要",
    raw_type="article",
    source="https://...",
    tags=["LLM"],
    user_notes="我的思考"
)

# 更新状态
processor.update_status(path, "compiled")
```

#### WikiBuilder
使用 LLM 将 Raw 材料编译为 Wiki 词条。支持英文内容的自动翻译。

```python
from src.compiler.wiki_builder import WikiBuilder

builder = WikiBuilder(raw_processor=processor, wiki_dir=Path("./wiki"))

# 编译单个 Raw 材料
created_paths = builder.compile(raw_path)

# 编译所有待处理材料
all_created = builder.compile_all_pending()
```

#### IndexGenerator
生成和维护 wiki/index.md 导航文件，支持增量更新。

```python
from src.compiler.index_generator import IndexGenerator

generator = IndexGenerator(wiki_dir=Path("./wiki"))

# 生成完整索引
index_path = generator.generate()

# 增量更新（添加新词条到索引）
generator.update_incremental(new_concepts)
```

#### LinkExtractor
提取和验证双向链接。

```python
from src.compiler.link_extractor import LinkExtractor

extractor = LinkExtractor(wiki_dir=Path("./wiki"))

# 构建链接图
extractor.build_link_graph()

# 查找断裂链接
broken = extractor.find_broken_links()

# 查找孤岛词条
orphaned = extractor.find_orphaned_entries()

# 获取相关词条
related = extractor.get_related_entries("Transformer", depth=2)
```

### src/query/

#### AgentQuery
执行深度查询。

```python
from src.query.agent_query import AgentQuery

agent = AgentQuery(wiki_dir=Path("./wiki"))

# 单次查询
answer = agent.query("什么是 Transformer？")
```

#### ContextManager
管理 Token 预算和上下文加载。

```python
from src.query.context_manager import ContextManager

context_mgr = ContextManager(
    wiki_dir=Path("./wiki"),
    token_budget=100000
)

# 为查询加载上下文
context = context_mgr.load_for_query("LLM 推理优化")
```

### src/maintenance/

#### HealthChecker
执行健康检查。

```python
from src.maintenance.health_checker import HealthChecker

checker = HealthChecker(wiki_dir=Path("./wiki"))

# 运行完整检查
results = checker.run_full_check()

# 生成报告
report = checker.generate_report(results)
```

---

## 配置说明

编辑 `config/wiki_config.yaml` 修改配置：

```yaml
model:
  default: "qwen3.6-plus"
  tasks:
    compilation: "qwen3.6-plus"
    analysis: "qwen3.6-plus"

context:
  query_budget: 100000

compilation:
  min_concepts: 3
  max_concepts: 8
  confidence_threshold: 0.7

health_check:
  outdated_days: 90
  enable_contradiction_check: true
```

---

## 最佳实践

### 1. Raw 材料质量

**好的 Raw 材料**：
- ✅ 包含明确的来源 URL
- ✅ 有你的手写思考和笔记
- ✅ 标签准确描述主题
- ✅ 内容精炼（1000-5000 字）

**避免**：
- ❌ 无来源的碎片信息
- ❌ 过长的全文（建议摘要 + 关键段落）
- ❌ 没有你的思考

### 2. 编译频率

建议批量编译：
- 积累 5-10 篇 Raw 材料后执行一次编译
- 编译后检查生成的 Wiki 词条质量
- 定期（每周）运行健康检查

### 3. 查询优化

获得更好查询结果：
- ✅ 问题具体明确
- ✅ 使用索引中的主题名称
- ✅ 对复杂主题使用连续追问

### 4. 知识维护

定期运行健康检查，关注：
- 🔴 断裂链接 - 需要创建缺失的词条
- ⚪ 孤岛词条 - 需要添加链接或删除
- ⚠️ 潜在矛盾 - 需要人工审核
- 📦 缺少来源 - 需要补充引用

---

## 故障排除

### 编译失败

**问题**: `Failed to extract concepts`

**解决**:
1. 检查 Raw 材料格式是否正确
2. 确认 frontmatter 包含必需的 `type` 字段
3. 检查 API Key 配置

### 查询结果为空

**问题**: 回答"暂无相关上下文"

**解决**:
1. 确认 wiki/concepts/ 下有相关词条
2. 运行 `compile_raw.py --all` 编译更多材料
3. 尝试使用不同的关键词

### Token 预算超限

**问题**: `Token budget reached`

**解决**:
1. 在 `config/wiki_config.yaml` 中增加 `query_budget`
2. 优化 index.md 结构，减少不必要条目

---

## 相关文档

- [docs/AGENTIC_WIKI_GUIDE.md](./docs/AGENTIC_WIKI_GUIDE.md) - 完整架构指南
- [docs/OBSIDIAN_WIKI_STRUCTURE.md](./docs/OBSIDIAN_WIKI_STRUCTURE.md) - Obsidian 集成指南

---

*最后更新：2026-04-13*
