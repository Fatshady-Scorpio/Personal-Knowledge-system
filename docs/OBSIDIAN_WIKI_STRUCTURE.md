# Obsidian Wiki Structure

**Last updated:** 2026-06-26

## Canonical Vault

`/Users/samcao/Obsidian/wiki`

This is the active personal knowledge base. It is not a generated preview folder and it should not depend on legacy project directories.

## Directory Structure

```text
/Users/samcao/Obsidian/wiki/
├── 00_inbox/
├── 10_sources/
│   ├── articles/
│   ├── papers/
│   ├── books/
│   ├── videos/
│   ├── conversations/
│   ├── research_reports/
│   ├── work_notes/
│   └── clippings/
├── 20_knowledge/
│   ├── domains/
│   │   ├── ai_agents/
│   │   ├── product_growth/
│   │   ├── business_investment/
│   │   ├── personal_systems/
│   │   ├── engineering/
│   │   └── content_creation/
│   ├── people_orgs/
│   └── glossary/
├── 30_projects/
├── 40_outputs/
├── 50_maps/
├── 90_archive/
└── _system/
    ├── indexes/
    ├── manifests/
    ├── migrations/
    ├── templates/
    └── reports/
```

## Separation Of Concerns

Obsidian vault:

- stores sources, knowledge, projects, outputs, maps, and machine indexes.
- is the source of truth.
- is readable and editable by Sam.

Personal Knowledge project:

- stores Python code, tests, configuration, and docs.
- ingests sources into the vault.
- compiles sources into maintained knowledge pages.
- builds indexes and context packs.
- runs maintenance checks.

Command Center:

- creates and tracks tasks.
- invokes the local runner for local vault writes.
- displays review cards and deposit reports.

## No Legacy Dependency

The old project layout used paths such as `raw/`, `wiki/concepts/`, and project-local `knowledge/**`. Those paths are historical only.

New code and documentation should target the v2 vault:

- sources: `/Users/samcao/Obsidian/wiki/10_sources`
- knowledge: `/Users/samcao/Obsidian/wiki/20_knowledge`
- outputs: `/Users/samcao/Obsidian/wiki/40_outputs`
- indexes: `/Users/samcao/Obsidian/wiki/_system/indexes`

## Common Commands

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src python scripts/search_v2.py --build --config config/vault.yaml
PYTHONPATH=src python scripts/search_v2.py Agent 记忆 --domain ai_agents --top-k 5 --config config/vault.yaml
PYTHONPATH=src pytest tests/unit -q
```

## Review Expectations

After an automated ingest or maintenance pass, Sam should be able to inspect:

- source file path
- created knowledge pages
- updated knowledge pages
- skipped duplicate sources
- candidate pages needing review
- affected indexes
