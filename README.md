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
- [ ] Phase 2: 自动采集 + 知识图谱
- [ ] Phase 3: 语义检索 + RAG 问答
- [ ] Phase 4: Agent 深度集成
