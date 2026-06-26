from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from personal_knowledge.migration.inventory import InventoryItem, collect_markdown_inventory
from personal_knowledge.migration.normalize import normalize_markdown
from personal_knowledge.migration.path_mapper import map_legacy_path


@dataclass(frozen=True)
class MigrationReport:
    scanned_count: int
    migrated_count: int
    staging_vault: str


def _reset_staging(staging_vault: Path) -> None:
    if staging_vault.exists():
        shutil.rmtree(staging_vault)
    for relative_dir in [
        "00_inbox/captures",
        "00_inbox/triage",
        "10_sources/articles",
        "10_sources/papers",
        "10_sources/books",
        "10_sources/videos",
        "10_sources/conversations",
        "10_sources/research_reports",
        "10_sources/work_notes",
        "10_sources/clippings",
        "20_knowledge/domains/ai_agents/concepts",
        "20_knowledge/domains/ai_agents/maps",
        "20_knowledge/domains/ai_agents/principles",
        "20_knowledge/domains/ai_agents/cases",
        "20_knowledge/domains/ai_agents/playbooks",
        "20_knowledge/domains/ai_agents/questions",
        "20_knowledge/domains/product_growth/concepts",
        "20_knowledge/domains/product_growth/maps",
        "20_knowledge/domains/business_investment/concepts",
        "20_knowledge/domains/business_investment/maps",
        "20_knowledge/domains/personal_systems/concepts",
        "20_knowledge/domains/personal_systems/maps",
        "20_knowledge/domains/engineering/concepts",
        "20_knowledge/domains/engineering/maps",
        "20_knowledge/domains/content_creation/concepts",
        "20_knowledge/domains/content_creation/maps",
        "20_knowledge/people_orgs",
        "20_knowledge/glossary",
        "30_projects/command_center",
        "30_projects/personal_knowledge_system",
        "30_projects/ai_research_digest",
        "30_projects/public_account",
        "40_outputs/research_reports",
        "40_outputs/public_articles",
        "40_outputs/briefs",
        "40_outputs/decisions",
        "50_maps",
        "90_archive",
        "_system/indexes",
        "_system/manifests",
        "_system/migrations",
        "_system/templates",
        "_system/reports",
    ]:
        (staging_vault / relative_dir).mkdir(parents=True, exist_ok=True)


def _unique_target_path(staging_vault: Path, target_rel: str, item: InventoryItem) -> tuple[str, Path]:
    target_path = staging_vault / target_rel
    if not target_path.exists():
        return target_rel, target_path

    suffix = item.content_hash[:10]
    candidate = target_path.with_name(f"{target_path.stem}__legacy-{suffix}{target_path.suffix}")
    return candidate.relative_to(staging_vault).as_posix(), candidate


def migrate_vault(current_vault: Path, staging_vault: Path, dry_run: bool) -> MigrationReport:
    items = collect_markdown_inventory(current_vault, ignored_dirs={".obsidian", ".trash"})
    if dry_run:
        return MigrationReport(scanned_count=len(items), migrated_count=0, staging_vault=str(staging_vault))

    _reset_staging(staging_vault)
    manifest_path = staging_vault / "_system" / "manifests" / "migration_manifest.jsonl"

    migrated = 0
    with manifest_path.open("w", encoding="utf-8") as manifest:
        for item in items:
            target_rel = map_legacy_path(item.relative_path)
            target_rel, target_path = _unique_target_path(staging_vault, target_rel, item)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            source_text = item.absolute_path.read_text(encoding="utf-8", errors="ignore")
            target_text = normalize_markdown(source_text, legacy_path=item.relative_path, target_path=target_rel)
            target_path.write_text(target_text, encoding="utf-8")
            manifest.write(
                json.dumps(
                    {
                        "source_path": item.relative_path,
                        "target_path": target_rel,
                        "content_hash": item.content_hash,
                        "size_bytes": item.size_bytes,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            migrated += 1

    report_path = staging_vault / "_system" / "reports" / "migration_report.md"
    report_path.write_text(
        f"# Migration Report\n\nScanned: {len(items)}\n\nMigrated: {migrated}\n",
        encoding="utf-8",
    )
    return MigrationReport(scanned_count=len(items), migrated_count=migrated, staging_vault=str(staging_vault))
