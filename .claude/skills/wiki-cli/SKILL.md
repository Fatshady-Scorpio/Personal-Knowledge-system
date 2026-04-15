---
name: wiki-cli
description: Query and compile the Personal Knowledge System wiki via CLI. Use when the user asks questions about their wiki knowledge base or wants to compile raw materials into wiki entries.
triggers: ["wiki query", "wiki compile", "wiki search", "what does my wiki know", "compile wiki", "knowledge base query"]
---

# Wiki CLI

Query and compile the Personal Knowledge System (Agentic Wiki). All operations are CLI-based — zero MCP overhead.

## Project Root

```
/Users/samcao/Documents/trae_projects/Personal Knowledge system
```

## When to Activate

- User asks a question that should be answered from their wiki knowledge base
- User wants to compile raw materials into structured wiki entries
- User wants to check wiki stats or health
- Triggers: "wiki query", "wiki compile", "wiki search", "what does my wiki know", "compile wiki"

## Operations

### 1. Query Wiki

Answer a question using the wiki knowledge base:

```bash
cd /Users/samcao/Documents/trae_projects/Personal\ Knowledge\ system
PYTHONPATH=. python scripts/query_wiki.py "用户的问题"
```

The output is the LLM-generated answer based on wiki content. Read the output and present it to the user.

**For interactive/complex queries:**

```bash
PYTHONPATH=. python scripts/query_wiki.py --interactive
```

### 2. Compile Raw Materials

Compile all pending raw materials into wiki entries:

```bash
cd /Users/samcao/Documents/trae_projects/Personal\ Knowledge\ system
PYTHONPATH=. python scripts/compile_raw.py --all --verbose
```

Compile a single raw file:

```bash
PYTHONPATH=. python scripts/compile_raw.py --file raw/articles/filename.md --verbose
```

### 3. Wiki Stats

Check current wiki state:

```bash
cd /Users/samcao/Documents/trae_projects/Personal\ Knowledge\ system
ls wiki/concepts/*.md 2>/dev/null | wc -l  # concept count
ls wiki/topics/*.md 2>/dev/null | wc -l   # topic count
test -f wiki/index.md && echo "index exists" || echo "no index"
ls raw/articles/*.md 2>/dev/null | wc -l  # pending raw count
```

### 4. Health Check

Run wiki health check:

```bash
cd /Users/samcao/Documents/trae_projects/Personal\ Knowledge\ system
PYTHONPATH=. python scripts/health_check.py --verbose
```

### 5. Chat API (long-running)

Start the HTTP API server for external integrations:

```bash
cd /Users/samcao/Documents/trae_projects/Personal\ Knowledge\ system
PYTHONPATH=. python scripts/start_chat_api.py --port 8000
```

## Architecture

- **Raw materials**: `raw/articles/` — user manually saved articles/notes
- **Wiki entries**: `wiki/concepts/` — LLM-compiled structured knowledge with `[[bilateral links]]`
- **Index**: `wiki/index.md` — hierarchical navigation map
- **Q&A**: `outputs/qa/` — saved query results for reuse
- **Model**: Uses Alibaba Cloud Bailian API via `src/utils/model_router.py`
- **Query engine**: `src/query/agent_query.py` — stateful wiki navigation + LLM answer generation

## Important

- The wiki is **manually curated** — no auto-collection or RSS. User saves raw materials manually.
- Compilation uses LLM to extract concepts and create wiki entries with bilateral links.
- Queries use `index.md` navigation + token-budget-aware context loading (not vector/RAG search).
- All CLI commands need `PYTHONPATH=.` prefix to resolve `src/` imports.
- Requires `BAILOU_API_KEY` environment variable for LLM calls.
