# Knowledge Structure V2

## Principle

The personal knowledge base is the durable source of truth for Sam's knowledge compounding system.

Research, reading, conversations, work notes, and future public-account drafts all feed the same vault. They differ by object type and lifecycle state, not by separate systems.

V2 preserves old data but does not preserve old code structure. The stable product is the Obsidian vault.

## Canonical Vault

`/Users/samcao/Obsidian/wiki`

## Directory Structure

```text
wiki/
├── 00_inbox/
│   ├── captures/
│   └── triage/
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
│   │   │   ├── concepts/
│   │   │   ├── maps/
│   │   │   ├── principles/
│   │   │   ├── cases/
│   │   │   ├── playbooks/
│   │   │   └── questions/
│   │   ├── product_growth/
│   │   ├── business_investment/
│   │   ├── personal_systems/
│   │   ├── engineering/
│   │   └── content_creation/
│   ├── people_orgs/
│   └── glossary/
├── 30_projects/
│   ├── command_center/
│   ├── personal_knowledge_system/
│   ├── ai_research_digest/
│   └── public_account/
├── 40_outputs/
│   ├── research_reports/
│   ├── public_articles/
│   ├── briefs/
│   └── decisions/
├── 50_maps/
│   ├── home.md
│   ├── domain_index.md
│   └── source_index.md
├── 90_archive/
└── _system/
    ├── indexes/
    ├── manifests/
    ├── migrations/
    ├── templates/
    └── reports/
```

## Layer Contracts

| Layer | Purpose | Write Policy |
| --- | --- | --- |
| `00_inbox` | temporary captures and ambiguous material | triaged regularly |
| `10_sources` | immutable inputs | body append/rewrite only with explicit review |
| `20_knowledge` | maintained knowledge objects | agent can update through reviewed protocol |
| `30_projects` | active work context | links to knowledge and sources |
| `40_outputs` | reports, briefs, article drafts, decisions | cite knowledge/source refs |
| `50_maps` | human navigation | agent maintains indexes and learning paths |
| `90_archive` | inactive retained material | rarely touched |
| `_system` | manifests, indexes, reports | machine maintained |

## Source Types

- `article`: external articles, blog posts, essays.
- `paper`: papers and technical PDFs.
- `book`: book notes and long-form reading.
- `video`: transcripts from video or audio sources.
- `conversation`: high-signal conversations that should become durable knowledge.
- `research_report`: research reports, work analysis, recurring task outputs.
- `work_note`: manual notes and quick captures.
- `clipping`: raw clipped pages.

Source frontmatter:

```yaml
---
type: source
source_type: research_report
title: Example
source_url:
source_id:
domain_hint: ai_agents
tags: []
status: raw
content_hash:
collected_at: 2026-06-26
legacy_path:
origin_task_id:
---
```

## Knowledge Object Types

- `concept`: atomic idea, definition, mechanism, vocabulary.
- `map`: MOC page that organizes a theme.
- `principle`: durable rule or heuristic Sam can reuse.
- `case`: concrete example, project incident, market event, product example.
- `playbook`: repeatable process or checklist.
- `question`: open problem or research question.
- `person_org`: people, companies, labs, products, institutions.
- `glossary`: short definitions and aliases.

Knowledge frontmatter:

```yaml
---
type: knowledge
object_type: concept
domain: ai_agents
title: Example
aliases: []
source_refs: []
status: candidate
confidence: 0.8
created_at: 2026-06-26
updated_at: 2026-06-26
reviewed_at:
legacy_path:
---
```

## Domains

- `ai_agents`: AI, LLM, agents, research methods, model behavior, tool use, automation.
- `product_growth`: product thinking, growth, ads, marketplace, user behavior, strategy.
- `business_investment`: company analysis, markets, capital, geopolitics when investment-relevant.
- `personal_systems`: workflows, decision systems, learning systems, productivity, knowledge operations.
- `engineering`: software architecture, infra, local/cloud deployment, observability, developer tooling.
- `content_creation`: public account topics, article arguments, writing assets, audience positioning.

Legacy domain mapping:

```yaml
ai: ai_agents
product: product_growth
investment: business_investment
general: personal_systems
```

## Naming Rules

Use stable readable filenames:

- Prefer Chinese titles when the concept is naturally Chinese in Sam's work.
- Prefer English canonical names for English technical terms, products, companies, papers, and models.
- Replace `/`, `:`, `?`, `*`, `"`, `<`, `>`, `|` with safe separators.
- Keep one page per durable object, not one page per mention.
- Use aliases for alternate names instead of duplicate pages.

## Maintenance Rules

- Raw source bodies are immutable after capture.
- Structured knowledge entries keep `legacy_path` during migration.
- Existing concept entries should be merged before creating duplicates.
- Generated entries default to `status: candidate`.
- Stable or reviewed entries should not be materially rewritten without review.
- Retrieval indexes live under `_system/indexes`.
- Migration manifests live under `_system/manifests`.
- Maintenance reports live under `_system/reports`.

## Retrieval Rules

- Search by domain first, then expand through links.
- Prefer `reviewed` and `stable` pages for task context.
- Include `candidate` pages only when marked clearly.
- Load only maps and top-k results into prompts.
- Cite local file paths when answers rely on the vault.
