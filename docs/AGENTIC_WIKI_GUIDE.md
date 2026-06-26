# Agentic Wiki Guide

## Mental Model

This project is no longer a legacy `raw/ -> concepts/` compiler. It is Sam's local LLM-maintained Obsidian wiki.

The operating loop is:

```text
capture source -> write immutable source -> compile durable knowledge -> weave links/maps -> index -> retrieve for work -> save good answers back
```

## Canonical Paths

- Vault: `/Users/samcao/Obsidian/wiki`
- Project: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor`
- Config: `config/vault.yaml`
- Source layer: `10_sources`
- Knowledge layer: `20_knowledge`
- System indexes: `_system/indexes`

## Ingest A Source

Create a JSON payload:

```json
{
  "source_id": "manual_2026_06_26_ai_agents_note",
  "title": "Agent 记忆分层笔记",
  "body": "# Agent 记忆分层笔记\n\n长期知识应该进入 Obsidian，短期任务状态可以留在任务系统。",
  "source_type": "work_note",
  "domain_hint": "ai_agents",
  "tags": ["agent", "memory"],
  "source_url": ""
}
```

Run:

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src python scripts/ingest_source.py --payload /path/to/payload.json --config config/vault.yaml
```

Expected result:

- a Markdown source under `/Users/samcao/Obsidian/wiki/10_sources/**`
- a content hash in frontmatter
- duplicate-safe behavior for identical content

## Compile A Source

Use a real source path returned by ingest:

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src python scripts/compile_source.py \
  --source "/Users/samcao/Obsidian/wiki/10_sources/work_notes/example.md" \
  --config config/vault.yaml
```

Expected result:

- useful durable pages under `20_knowledge/domains/{domain}/**`
- `source_refs` back to the source
- generated entries marked `candidate`
- source status moved toward `compiled`

## Build Or Search Indexes

Build all domain indexes:

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src python scripts/search_v2.py --build --config config/vault.yaml
```

Search a domain:

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src python scripts/search_v2.py Agent 记忆 --domain ai_agents --top-k 5 --config config/vault.yaml
```

Expected result:

- search reads per-domain indexes from `_system/indexes`
- output paths point to `20_knowledge/domains/ai_agents/**`

## Command Center Deposit Flow

The preferred production path is not manual CLI use.

1. Research or secretary agent creates/finishes work.
2. Sam chooses `沉淀到知识库` or the task policy requests deposit.
3. Command Center creates `knowledge_deposit`.
4. Local Knowledge Runner calls `scripts/ingest_source.py`.
5. Local Knowledge Runner calls `scripts/compile_source.py`.
6. Local Knowledge Runner calls `scripts/search_v2.py --build`.
7. Deposit report returns created, updated, skipped, and review-required pages.

## Daily Operating Rules

- Research is only one knowledge source. Manual notes, conversations, and project learnings use the same deposit path.
- Good answers should be promoted into knowledge when they contain reusable synthesis.
- Ambiguous user requests should trigger a clarification question rather than guessing.
- `candidate` pages can be used but must be marked as candidate in high-impact context.
- Stable knowledge should cite source files or explicitly state that it is Sam's synthesis.

## Maintenance Cadence

Per ingest:

- write source
- compile source
- update touched maps
- rebuild affected indexes
- append operation report

Daily:

- triage `00_inbox`
- list uncompiled sources
- check recently touched maps

Weekly:

- detect duplicate concepts
- detect orphan pages
- find stale or low-confidence knowledge
- report sources that never compiled

Monthly:

- review domain maps
- promote stable principles/cases
- archive inactive project notes
- update public-account backlog
