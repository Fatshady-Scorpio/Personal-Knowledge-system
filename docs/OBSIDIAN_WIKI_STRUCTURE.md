# Obsidian Wiki 目录结构

**最后更新**: 2026-04-08

## 目录结构

```
/Users/samcao/Obsidian/wiki/          # Obsidian 知识库主目录（实际存储）
├── index.md                          # 知识库导航索引
├── concepts/                         # 概念词条（双向链接节点）
│   ├── Transformer.md
│   ├── 大语言模型.md
│   └── ...
└── topics/                           # 主题 MOC（Map of Content）
    └── ...

/Users/samcao/Documents/trae_projects/Personal Knowledge system/
├── raw/                              # 原始材料（待编译）
│   ├── articles/
│   ├── videos/
│   ├── papers/
│   └── notes/
├── wiki/                             # 符号链接 → /Users/samcao/Obsidian/wiki
├── src/                              # 编译源代码
├── scripts/                          # 执行脚本
├── docs/                             # 项目文档
└── config/                           # 配置文件
```

## 设计说明

### 为什么分离？

1. **Obsidian Wiki 目录** - 只存储实际的知识内容
   - `concepts/` - 概念词条
   - `topics/` - 主题索引
   - `index.md` - 导航目录

2. **项目目录** - 存储工具和配置
   - 编译脚本
   - 自动调度器
   - 配置文档
   - Raw 材料

### 符号链接的作用

`/Users/samcao/Documents/trae_projects/Personal Knowledge system/wiki` 
是一个符号链接，实际指向 `/Users/samcao/Obsidian/wiki/`

这样设计的好处：
- ✅ Obsidian 打开的是纯净的知识库，没有代码文件
- ✅ 编译脚本可以通过符号链接写入 wiki
- ✅ 两个目录解耦，各司其职

## 使用流程

```
1. 浏览网页 → 用 Web Clipper 剪藏到 raw/articles/
2. 添加 frontmatter: ---
                      type: article
                      ---
3. 自动编译调度器检测 → 编译成 Wiki 词条 → 写入 /Users/samcao/Obsidian/wiki/
4. Obsidian 自动刷新 → 查看新生成的词条
```

## 命令参考

```bash
# 编译所有待处理的 Raw 材料
PYTHONPATH=. python scripts/start_auto_compile.py --run-once

# 启动自动编译调度器
PYTHONPATH=. python scripts/start_auto_compile.py

# 查看 Raw 目录待编译文件数量
ls raw/articles/*.md | wc -l

# 查看 Wiki 词条数量
ls /Users/samcao/Obsidian/wiki/concepts/*.md | wc -l
```

## Raw 材料格式

**最简格式**（推荐 Web Clipper 用户）：
```markdown
---
type: article
---

[剪藏内容]
```

**完整格式**：
```markdown
---
type: article
source: https://example.com
collected_at: 2026-04-08
tags: [LLM, RAG]
status: raw
---

# 文章标题

[内容]

---

## 我的思考

[你的笔记]
```

## 批量修复工具

如果你用 Web Clipper 剪藏了很多内容，运行：

```bash
cd /Users/samcao/Documents/trae_projects/Personal\ Knowledge\ system
PYTHONPATH=. python scripts/fix_webclipper_import.py
```

---

*此文档解释 Obsidian Wiki 目录结构的设计理念*
