# Agentic Wiki 使用指南

## 快速开始（5 分钟上手）

### 第一步：创建你的第一篇 Raw 材料

1. 在 `raw/articles/` 目录下创建一个新的 markdown 文件：

```bash
# 方式 1：手动创建
cat > raw/articles/20260407_我的第一篇笔记.md << 'EOF'
---
type: note
title: 我的第一篇笔记
collected_at: 2026-04-07
tags: [测试，入门]
status: raw
---

# 我的第一篇笔记

这是我对某个主题的理解和思考。

## 核心观点

1. 观点一
2. 观点二
3. 观点三

---

## 我的思考

我觉得这个主题很有意思，因为...
EOF
```

```bash
# 方式 2：使用 Python 创建
PYTHONPATH=. python << 'EOF'
from src.compiler.raw_processor import RawProcessor
from pathlib import Path

processor = RawProcessor(Path("raw"))
processor.create(
    title="我的第一篇笔记",
    content="这是我对某个主题的理解和思考。",
    raw_type="note",
    tags=["测试", "入门"],
    user_notes="我觉得这个主题很有意思，因为..."
)
EOF
```

### 第二步：编译为 Wiki 词条

```bash
PYTHONPATH=. python scripts/compile_raw.py --all --verbose
```

执行后，你会在 `wiki/concepts/` 目录下看到生成的词条文件。

### 第三步：查看生成的 Wiki

```bash
# 查看生成的词条
ls -la wiki/concepts/

# 查看索引文件
cat wiki/index.md

# 或用 Obsidian 打开
open wiki/
```

### 第四步：查询知识库

```bash
# 交互式查询
PYTHONPATH=. python scripts/query_wiki.py --interactive
```

---

## 日常工作流

### 场景 1：阅读到好文章

```
1. 阅读文章 → 2. 保存为 Raw → 3. 积累几篇后编译 → 4. 查询时复用
```

**具体操作**：

```bash
# 1. 保存文章（手动创建 markdown）
cat > raw/articles/20260407_LLM 推理优化.md << 'EOF'
---
type: article
source: https://example.com/llm-inference
collected_at: 2026-04-07
tags: [LLM, 推理优化]
status: raw
---

# LLM 推理优化技术总结

## 主要内容

文章介绍了以下几种优化技术：

1. **量化**：FP16/INT8/FP8 量化
2. **注意力优化**：PagedAttention、FlashAttention
3. **批处理**：Continuous Batching

## 关键数据

- INT8 量化可减少 50% 显存
- PagedAttention 提升 24 倍吞吐

---

## 我的思考

这篇文章的量化部分讲得很清楚，但缺少实际代码示例。
我觉得可以结合 vLLM 的源码来理解。
EOF

# 2. 编译（可以积累几篇后一起编译）
PYTHONPATH=. python scripts/compile_raw.py --all

# 3. 之后查询时会自动使用这些知识
PYTHONPATH=. python scripts/query_wiki.py "LLM 推理优化有哪些技术？"
```

### 场景 2：观看视频后记录

```bash
# 保存视频笔记
PYTHONPATH=. python << 'EOF'
from src.compiler.raw_processor import RawProcessor
from pathlib import Path

processor = RawProcessor(Path("raw"))
processor.create(
    title="Karpathy Agentic Wiki 视频笔记",
    content="""
视频核心内容：

1. LLM Wiki 的三层结构：raw/ → wiki/ → outputs/
2. 双向链接的重要性
3. 知识复利的概念

关键引用：
- "RAG 是无状态的阅览室"
- "Wiki 是有状态的知识库"
""",
    raw_type="video",
    source="https://youtube.com/watch?v=xxx",
    tags=["知识管理", "LLM"],
    user_notes="""
这个理念和我之前的 RAG 思路完全不同，需要重新设计整个系统。
特别是 index.md 作为导航入口的设计很巧妙。
"""
)
EOF

# 编译
PYTHONPATH=. python scripts/compile_raw.py --all
```

### 场景 3：深度研究一个主题

```bash
# 启动交互式查询
PYTHONPATH=. python scripts/query_wiki.py --interactive

# 然后连续追问：
# ❓ 请问：什么是 LLM 推理优化？
# ❓ 请问：有哪些主流框架？
# ❓ 请问：vLLM 和 TGI 的区别？

# 查询结果会自动保存到 outputs/qa/
```

---

## 高级用法

### 1. 批量导入现有笔记

如果你有现有的 markdown 笔记：

```bash
# 1. 复制到 raw 目录
cp ~/notes/*.md raw/articles/

# 2. 批量添加 frontmatter（如果需要）
PYTHONPATH=. python << 'EOF'
from pathlib import Path

for md_file in Path("raw/articles").glob("*.md"):
    content = md_file.read_text()
    if not content.startswith("---"):
        # 添加 frontmatter
        frontmatter = """---
type: article
status: raw
tags: []
---

"""
        md_file.write_text(frontmatter + content)
EOF

# 3. 编译
PYTHONPATH=. python scripts/compile_raw.py --all
```

### 2. 自定义编译参数

```python
from src.compiler.wiki_builder import WikiBuilder
from src.compiler.raw_processor import RawProcessor
from pathlib import Path

processor = RawProcessor(Path("raw"))
builder = WikiBuilder(processor, Path("wiki"), model="qwen3.5-plus")

# 自定义模型参数
# 在 wiki_builder.py 中修改 call 参数
```

### 3. 定期健康检查

**手动运行**
```bash
# 每周运行一次
PYTHONPATH=. python scripts/health_check.py --output reports/health_$(date +%Y-%m-%d).md
```

**月度自动健康检查**（推荐）

启动月度健康检查调度器，每月 1 号上午 9:00 自动执行：

```bash
# 启动调度器（后台运行）
PYTHONPATH=. python scripts/start_monthly_health_check.py

# 仅运行一次
PYTHONPATH=. python scripts/start_monthly_health_check.py --run-once

# macOS 开机自启
bash deploy/setup_monthly_health_check.sh
```

健康检查项目：
1. 断裂链接 ([[link]] 指向不存在的词条)
2. 孤岛词条 (无双向链接的词条)
3. 潜在矛盾 (语义冲突)
4. 缺少来源 (无引用的断言)
5. 过期内容 (>90 天未更新)
6. 幻觉风险 (低置信度/模糊来源)

---

## 故障排除

### 问题 1：编译后没有生成词条

**可能原因**：
- Raw 材料格式不正确
- LLM API 调用失败
- 内容为空或太短

**解决方法**：
```bash
# 检查 Raw 材料格式
cat raw/articles/你的文件.md

# 确认有 frontmatter
head -10 raw/articles/你的文件.md

# 查看详细日志
PYTHONPATH=. python scripts/compile_raw.py --file 你的文件.md --verbose
```

### 问题 2：查询结果不准确

**可能原因**：
- Wiki 词条太少
- index.md 索引不完整
- 问题太模糊

**解决方法**：
```bash
# 1. 编译更多 Raw 材料
PYTHONPATH=. python scripts/compile_raw.py --all

# 2. 重新生成索引
PYTHONPATH=. python scripts/compile_raw.py --regenerate

# 3. 尝试更具体的问题
# ❌ "什么是 AI？"（太宽泛）
# ✅ "Transformer 的注意力机制是什么？"（具体）
```

### 问题 3：Token 预算超限

**症状**：`Token budget reached`

**解决方法**：
```yaml
# 编辑 config/wiki_config.yaml
context:
  query_budget: 150000  # 增加预算
```

---

## 最佳实践检查清单

### Raw 材料质量

- [ ] 包含明确的来源 URL
- [ ] 有自己的思考和笔记
- [ ] 标签准确描述主题
- [ ] 内容长度适中（1000-5000 字）
- [ ] frontmatter 格式正确

### 编译流程

- [ ] 积累 5-10 篇后批量编译
- [ ] 编译后检查生成的词条
- [ ] 定期重新生成 index.md
- [ ] 关注低置信度（<0.7）的词条

### 查询优化

- [ ] 问题具体明确
- [ ] 使用索引中的主题名称
- [ ] 复杂主题使用连续追问
- [ ] 保存高价值 Q&A

### 知识维护

- [ ] 每周运行健康检查
- [ ] 修复断裂链接
- [ ] 处理孤岛词条
- [ ] 审核潜在矛盾

---

## 示例：完整的知识积累循环

```
第 1 天：阅读文章
├─ 保存为 raw/articles/20260401_RAG 技术.md
└─ 添加个人思考

第 2 天：观看视频
├─ 保存为 raw/articles/20260402_LLM 应用.md
└─ 添加个人思考

第 3 天：阅读论文
├─ 保存为 raw/articles/20260403_Attention.md
└─ 添加个人思考

第 7 天：批量编译（积累了 7 篇）
├─ PYTHONPATH=. python scripts/compile_raw.py --all
├─ 生成 ~20 个 Wiki 词条
└─ 更新 index.md

第 14 天：深度查询
├─ python scripts/query_wiki.py --interactive
├─ 追问 5 个相关问题
└─ 保存到 outputs/qa/

第 30 天：健康检查
├─ python scripts/health_check.py
├─ 修复 2 个断裂链接
└─ 合并 1 个矛盾
```

---

## 下一步

- [ ] 创建你的第一篇 Raw 材料
- [ ] 运行第一次编译
- [ ] 尝试查询知识库
- [ ] 阅读 [CLAUDE.md](../CLAUDE.md) 了解更多

---

*最后更新：2026-04-07*
