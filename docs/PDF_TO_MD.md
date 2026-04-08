# PDF 转 Markdown 使用指南

将 PDF 文档转换为符合 Agentic Wiki 编译格式的 Markdown 文件。

---

## 安装依赖

首次使用前，安装必要的依赖：

```bash
pip install pdfplumber PyPDF2
```

或使用脚本内置的安装选项：

```bash
PYTHONPATH=. python scripts/pdf_to_md.py --install-deps
```

---

## 使用方法

### 1. 转换单个 PDF（推荐）

```bash
cd /Users/samcao/Documents/trae_projects/Personal\ Knowledge\ system
PYTHONPATH=. python scripts/pdf_to_md.py /path/to/paper.pdf
```

输出文件会自动保存到 `/Users/samcao/Obsidian/wiki/raw/papers/`

### 2. 转换到指定目录

```bash
PYTHONPATH=. python scripts/pdf_to_md.py /path/to/paper.pdf /Users/samcao/Obsidian/wiki/raw/articles/
```

### 3. 自定义标题和标签

```bash
PYTHONPATH=. python scripts/pdf_to_md.py paper.pdf \
  --title "大语言模型推理优化研究" \
  --tags "LLM，推理优化，性能"
```

### 4. 添加你的思考

```bash
PYTHONPATH=. python scripts/pdf_to_md.py paper.pdf \
  --notes "这篇文章提出了新的注意力机制，值得深入研究。"
```

### 5. 完整参数示例

```bash
PYTHONPATH=. python scripts/pdf_to_md.py paper.pdf \
  --title "Transformer 架构详解" \
  --tags "Transformer，注意力机制，深度学习" \
  --notes "对理解 LLM 架构很有帮助"
```

---

## 生成的文件格式

转换后的 Markdown 文件包含：

```markdown
---
type: article
title: 论文标题
source: file:///path/to/paper.pdf
collected_at: 2026-04-08T16:00:00
tags: [PDF, 机器学习，AI]
status: raw
---

# 论文标题

[从 PDF 提取的正文内容]

---

## 我的思考

[如果你在 --notes 中添加了思考]
```

---

## 输出目录

| PDF 类型 | 默认输出目录 |
|----------|-------------|
| 学术论文 | `raw/papers/` |
| 普通文章 | `raw/articles/` |
| 视频转录 | `raw/videos/` |
| 临时笔记 | `raw/notes/` |

---

## 依赖库对比

| 库 | 优点 | 缺点 |
|----|------|------|
| **pdfplumber** (推荐) | 提取质量高，支持表格 | 稍慢 |
| **PyPDF2** (备选) | 轻量，快速 | 复杂 PDF 可能提取不完整 |

脚本会自动优先使用 pdfplumber，如果未安装则回退到 PyPDF2。

---

## 常见问题

### Q: 提取的文本格式混乱
A: PDF 格式复杂，建议：
- 检查生成的 MD 文件，手动调整格式
- 在 `--notes` 中添加你的理解

### Q: 扫描件/图片 PDF 无法提取
A: 需要 OCR 功能，当前不支持。建议：
- 使用其他 OCR 工具（如 Adobe Acrobat）先转为文本
- 或手动输入关键内容

### Q: 如何批量转换？
A: 使用 shell 脚本批量处理：

```bash
for pdf in /path/to/pdfs/*.pdf; do
  PYTHONPATH=. python scripts/pdf_to_md.py "$pdf"
done
```

---

## 下一步

转换后的文件会自动进入待编译队列：
1. 调度器检测到新文件（`status: raw`）
2. 当满足条件时自动编译（≥5 个文件或≥24 小时）
3. 生成 Wiki 词条到 `wiki/concepts/`
4. 更新 `wiki/index.md` 导航

你也可以手动触发编译：

```bash
PYTHONPATH=. python scripts/compile_raw.py --all
```
