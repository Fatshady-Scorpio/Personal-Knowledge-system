# Personal Knowledge System - 自动化使用指南

## 快速开始（5 分钟设置）

### 第一步：安装依赖

```bash
pip install -r requirements.txt
```

### 第二步：配置你的兴趣

编辑 `config/user_interests.yaml`：

```yaml
interests:
  keywords:
    - LLM           # 你感兴趣的主题
    - RAG
    - Agent
    - 多模态
    
ignore_keywords:
  - 广告            # 自动忽略的内容
  - 推广
```

### 第三步：测试运行

```bash
# 手动触发一次完整流程
python scripts/start_scheduler.py --run-once
```

运行后检查：
- `knowledge/20-Processed/` - 新增的笔记
- `knowledge/50-Outputs/daily_briefing_*.md` - 每日简报

### 第四步：启动自动调度

```bash
# 启动调度服务（前台运行）
python scripts/start_scheduler.py
```

服务会每天 9:00 自动执行知识采集任务。

### 第五步：设置开机自启（macOS）

```bash
# 复制启动配置
cp deploy/com.personal.kb.plist ~/Library/LaunchAgents/

# 加载配置
launchctl load ~/Library/LaunchAgents/com.personal.kb.plist

# 验证
launchctl list | grep personal
```

---

## 日常使用

### 你只需要：

1. **打开 Obsidian**
2. **查看「50-Outputs」文件夹**
3. **阅读最新的「每日简报」**

### 每日简报示例：

```markdown
# 每日 AI 简报 - 2026-04-05

## 今日概览
- 处理文章：8 篇
- 新增笔记：8 条
- 更新主题：3 个

## 精选内容

### LLM
- [大模型推理优化技术](path/to/note.md)
  > 本文介绍了最新的 LLM 推理优化技术...

### RAG
- [RAG 系统架构设计](path/to/note.md)
  > RAG 系统的设计模式和最佳实践...

## 知识图谱更新
- 新增关联：15 条
```

---

## 自定义配置

### 修改采集时间

编辑 `config/schedule.yaml`：

```yaml
daily_collection:
  hour: 8      # 改为早上 8 点
  minute: 30
```

### 添加自定义 RSS 源

编辑 `config/sources.yaml`：

```yaml
custom:
  rss_feeds:
    - name: "我的博客"
      url: "https://example.com/feed.xml"
      category: "AI"
      priority: high
```

### 调整优先级规则

编辑 `src/processor/priority_filter.py` 或 `config/user_interests.yaml`：

```yaml
# 高优先级源（必处理）
high_priority_sources:
  - 机器之心 RSS
  - arXiv cs.AI
  
# 兴趣关键词（匹配越多优先级越高）
keywords:
  - Transformer
  - 大模型
```

---

## 故障排查

### 查看日志

```bash
# 调度器日志
cat scheduler.log

# 系统日志
tail -f /tmp/personal-kb-scheduler.log
```

### 手动测试单个组件

```bash
# 测试 RSS 抓取
python -c "from src.collector import RSSFetcher; f = RSSFetcher(); print(f.fetch('https://www.jiqizhixin.com/rss', 3))"

# 测试优先级过滤
python -c "from src.processor.priority_filter import PriorityFilter; f = PriorityFilter(); print(f.should_process({'title': 'LLM 最新进展', 'name': '机器之心 RSS'}))"

# 测试简报生成
python -c "from src.processor.briefing import DailyBriefing; b = DailyBriefing(); print(b.generate())"
```

### 常见问题

**Q: 没有生成简报？**
- 检查 `knowledge/20-Processed/` 是否有内容
- 简报只在有内容处理时生成

**Q: 内容太少/太多？**
- 调整 `config/user_interests.yaml` 中的过滤规则
- 修改 RSS 源数量

**Q: 调度器没有运行？**
- macOS: `launchctl list | grep personal` 检查状态
- 手动运行 `python scripts/start_scheduler.py` 测试

---

## 系统架构

```
┌─────────────────────────────────────────┐
│         定时调度器 (9:00 AM)             │
└─────────────────┬───────────────────────┘
                  │
         ┌────────▼────────┐
         │  优先级过滤器    │
         └────────┬────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌────────┐   ┌────────┐   ┌────────┐
│ RSS 源  │   │ RSS 源  │   │ RSS 源  │
│ 机器之心│   │ arXiv  │   │ 自定义 │
└────┬───┘   └────┬───┘   └────┬───┘
     │           │             │
     └───────────┼─────────────┘
                 │
         ┌───────▼───────┐
         │  摘要生成器    │
         │  分类器        │
         │  知识图谱      │
         └───────┬───────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│20-Processed│ │30-Topics │ │50-Outputs│
│  自动笔记  │ │  主题分类 │ │  每日简报 │
└──────────┘ └──────────┘ └──────────┘
                (Obsidian 自动同步)
```

---

## 预配置内容源

系统已预配置以下高质量 AI 内容源：

### 国内媒体
- 机器之心 RSS
- 量子位 RSS
- 机器之心论文

### 国外媒体
- Hacker News AI
- arXiv cs.AI (最新论文)
- arXiv cs.LG (机器学习)
- Sebastian Raschka (AI 教育者)
- Jay Alammar (可视化 AI 讲解)

你可以根据需要添加或删除这些源。
