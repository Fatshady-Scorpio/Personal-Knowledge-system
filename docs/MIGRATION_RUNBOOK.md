# Migration Runbook

## Principle

Migration is data-first. Preserve useful old data and traceability; do not preserve old code as a product constraint.

The v2 source of truth is:

`/Users/samcao/Obsidian/wiki`

The old repository layout, old `raw/` flow, old server, and old compiler/search modules can be archived or ignored once their data has been migrated.

## Fresh Migration Commands

Use these only when rebuilding a staging vault from legacy data:

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src python scripts/migrate_v2.py inventory
PYTHONPATH=src python scripts/migrate_v2.py dry-run
PYTHONPATH=src python scripts/migrate_v2.py migrate
PYTHONPATH=src python scripts/migrate_v2.py validate
```

The migrator writes staging output before cutover. It must not mutate the canonical vault during dry runs.

## Review Checklist

- Source markdown count matches the migration report.
- Staging vault opens in Obsidian.
- Domain indexes render.
- Sampled concept pages keep their source links or `legacy_path`.
- Sampled source pages keep their original body content.
- `_system/manifests/migration_manifest.jsonl` exists.
- No path escapes the staging vault.

## Cutover

Cutover is manual and requires explicit approval:

```bash
mv /Users/samcao/Obsidian/wiki /Users/samcao/Obsidian/wiki-legacy-$(date +%Y%m%d)
mv /Users/samcao/Obsidian/wiki-v2-staging /Users/samcao/Obsidian/wiki
```

## Post-Cutover Legacy Cleanup

After the canonical vault has migrated data:

1. Keep `/Users/samcao/Obsidian/wiki` as the only active vault.
2. Archive old local data directories into a local ignored archive when needed.
3. Remove stale worktree metadata with `git worktree prune --verbose`.
4. Keep `.local-archive/`, `.claude/worktrees/`, and local vault links ignored.
5. Do not spend time adapting old scripts unless they contain behavior still needed by v2.

## Verification Commands

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src pytest tests/unit -q
PYTHONPATH=src python scripts/search_v2.py Agent 记忆 --domain ai_agents --top-k 5 --config config/vault.yaml
```

Expected:

- unit tests pass.
- search returns relevant `20_knowledge/domains/ai_agents/**` pages.

## Archive Rule

Archive or delete old files only after these are true:

- migrated content exists in `/Users/samcao/Obsidian/wiki`.
- `legacy_path` or manifest entries preserve traceability.
- current v2 scripts can ingest, compile, index, and search.
- Sam has confirmed old code compatibility is not required.
