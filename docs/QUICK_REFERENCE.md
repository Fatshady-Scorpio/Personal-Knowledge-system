# Agentic Wiki 快速参考

## 核心工作流

```
保存 Raw → 自动/手动编译 → 聊天查询 → 定期健康检查
```

---

## 常用命令

### 保存 Raw 材料

```bash
# 保存到 raw/articles/ 目录
# 格式参考 docs/AGENTIC_WIKI_GUIDE.md
```

### 编译

```bash
# 【手动】编译所有待处理文件
PYTHONPATH=. python scripts/compile_raw.py --all

# 【手动】编译单个文件
PYTHONPATH=. python scripts/compile_raw.py --file raw/articles/文件名.md

# 【自动】启动自动编译调度器
PYTHONPATH=. python scripts/start_auto_compile.py

# 【自动】后台运行（推荐）
nohup python scripts/start_auto_compile.py > /tmp/wiki-compile.log 2>&1 &

# 查看编译日志
tail -f /tmp/wiki-auto-compile.out.log
```

### 查询/聊天

```bash
# 【推荐】交互式聊天
PYTHONPATH=. python scripts/chat.py

# 命令行查询
PYTHONPATH=. python scripts/query_wiki.py "你的问题"

# 查询不保存结果
PYTHONPATH=. python scripts/query_wiki.py "你的问题" --no-save
```

### 健康检查

```bash
# 运行健康检查
PYTHONPATH=. python scripts/health_check.py

# 保存报告
PYTHONPATH=. python scripts/health_check.py --output reports/health.md
```

---

## 自动编译配置

### 触发条件（满足任一即可）

| 条件 | 默认值 | 说明 |
|------|--------|------|
| 文件数量 | ≥ 5 个 | 待编译文件达到阈值 |
| 等待时间 | ≥ 24 小时 | 距离上次编译的时间 |
| 强制编译 | 每天 22:00 | 如果有待处理文件 |

### 自定义参数

```bash
# 3 个文件就编译，12 小时强制，每 15 分钟检查
PYTHONPATH=. python scripts/start_auto_compile.py \
    --min-files 3 \
    --max-wait 12 \
    --check-every 15
```

### macOS 开机自启

```bash
# 安装
cp deploy/com.personal.wiki-auto-compile.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.personal.wiki-auto-compile.plist

# 卸载
launchctl unload ~/Library/LaunchAgents/com.personal.wiki-auto-compile.plist
rm ~/Library/LaunchAgents/com.personal.wiki-auto-compile.plist
```

---

## 聊天模式命令

在 `scripts/chat.py` 交互式聊天中可用：

| 命令 | 功能 |
|------|------|
| `help` | 显示帮助 |
| `stats` | 显示知识库统计 |
| `history` | 显示问答历史 |
| `quit` / `exit` / `q` | 退出 |

---

## 文件位置

| 类型 | 目录 |
|------|------|
| Raw 材料 | `raw/articles/` |
| Wiki 词条 | `wiki/concepts/` |
| 主题 MOC | `wiki/topics/` |
| 索引导航 | `wiki/index.md` |
| 问答记录 | `outputs/qa/` |

---

## 典型使用场景

### 场景 1：阅读到好文章

```bash
# 1. 保存为 Raw（手动创建 markdown）
cat > raw/articles/20260407_文章标题.md << 'EOF'
---
type: article
source: https://example.com/article
tags: [主题，标签]
---

# 标题

[内容摘要]

---

## 我的思考

[个人笔记]
EOF

# 2. 等待自动编译（或手动触发）
PYTHONPATH=. python scripts/compile_raw.py --all

# 3. 之后查询时会用到
PYTHONPATH=. python scripts/chat.py
```

### 场景 2：批量处理

```bash
# 周末一次性处理一周积累的文章
# 假设 raw/articles/ 已经有 10 篇待编译

# 手动编译
PYTHONPATH=. python scripts/compile_raw.py --all

# 或启动自动编译，让它后台处理
PYTHONPATH=. python scripts/start_auto_compile.py --run-once
```

### 场景 3：深度研究

```bash
# 1. 启动聊天
PYTHONPATH=. python scripts/chat.py

# 2. 连续追问
❓ 你：什么是 LLM 推理优化？
💡 助手：[回答]

❓ 你：有哪些主流框架？
💡 助手：[回答]

❓ 你：vLLM 和 TGI 的区别？
💡 助手：[回答]

# 3. 问答自动保存到 outputs/qa/
```

---

## 配置调优

编辑 `config/wiki_config.yaml`：

```yaml
# 增加查询 Token 预算
context:
  query_budget: 150000

# 降低编译触发阈值
compilation:
  min_concepts: 2
  max_concepts: 10

# 关闭矛盾检测（加快速度）
health_check:
  enable_contradiction_check: false
```

---

## 故障排查

| 问题 | 解决 |
|------|------|
| 编译没有生成词条 | 检查 `wiki/concepts/` 目录，查看日志 |
| 查询结果为空 | 先编译更多 Raw 材料 |
| 自动编译不触发 | 检查是否有 pending 文件：`ls raw/articles/*.md` |
| Token 超限 | 增加 `config/wiki_config.yaml` 中的 `query_budget` |

---

*最后更新：2026-04-07*
