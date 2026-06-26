import json
from pathlib import Path

from personal_knowledge.migration.migrator import migrate_vault


def test_migrate_vault_writes_staging_and_manifest(tmp_path: Path):
    current = tmp_path / "current"
    staging = tmp_path / "staging"
    (current / "domains" / "ai" / "concepts").mkdir(parents=True)
    (current / "domains" / "ai" / "concepts" / "Transformer.md").write_text("# Transformer", encoding="utf-8")

    report = migrate_vault(current_vault=current, staging_vault=staging, dry_run=False)

    target = staging / "20_knowledge" / "domains" / "ai_agents" / "concepts" / "Transformer.md"
    manifest = staging / "_system" / "manifests" / "migration_manifest.jsonl"

    assert report.migrated_count == 1
    assert (staging / "00_inbox" / "captures").is_dir()
    assert (staging / "30_projects" / "public_account").is_dir()
    assert (staging / "50_maps").is_dir()
    assert target.exists()
    assert manifest.exists()
    assert json.loads(manifest.read_text().splitlines()[0])["target_path"].endswith("Transformer.md")


def test_migrate_vault_preserves_colliding_targets(tmp_path: Path):
    current = tmp_path / "current"
    staging = tmp_path / "staging"
    (current / "domains" / "general" / "concepts").mkdir(parents=True)
    (current / "wiki" / "concepts").mkdir(parents=True)
    (current / "domains" / "general" / "concepts" / "Decision.md").write_text("# A", encoding="utf-8")
    (current / "wiki" / "concepts" / "Decision.md").write_text("# B", encoding="utf-8")

    report = migrate_vault(current_vault=current, staging_vault=staging, dry_run=False)
    migrated_files = list((staging / "20_knowledge" / "domains" / "personal_systems" / "concepts").glob("*.md"))

    assert report.migrated_count == 2
    assert len(migrated_files) == 2
