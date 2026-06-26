import json
from pathlib import Path

from personal_knowledge.config import VaultConfig
from personal_knowledge.ingest.source_writer import SourceWriteRequest, SourceWriter


def test_source_writer_writes_source_manifest_and_operation_log(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    writer = SourceWriter(config)

    result = writer.write(
        SourceWriteRequest(
            source_id="task_123",
            title="AI Report",
            body="# Report\n\nUseful content",
            source_type="research_report",
            domain_hint="ai",
            source_url="https://example.test/report",
            tags=["AI", "research"],
        )
    )

    assert result.status == "created"
    assert result.path == config.research_reports_dir / "AI_Report-task_123.md"
    assert result.path.exists()
    assert "type: source" in result.path.read_text(encoding="utf-8")
    assert "domain_hint: ai_agents" in result.path.read_text(encoding="utf-8")

    manifest_lines = config.knowledge_manifest_path.read_text(encoding="utf-8").splitlines()
    assert len(manifest_lines) == 1
    assert json.loads(manifest_lines[0])["source_id"] == "task_123"

    operation_lines = config.operation_log_path.read_text(encoding="utf-8").splitlines()
    assert len(operation_lines) == 1
    assert json.loads(operation_lines[0])["event"] == "source_created"


def test_source_writer_skips_duplicate_content_hash(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    writer = SourceWriter(config)
    request = SourceWriteRequest(
        source_id="task_123",
        title="AI Report",
        body="# Report\n\nUseful content",
        source_type="research_report",
        domain_hint="ai",
    )

    first = writer.write(request)
    second = writer.write(request)

    assert first.status == "created"
    assert second.status == "duplicate"
    assert second.path == first.path
    assert len(config.knowledge_manifest_path.read_text(encoding="utf-8").splitlines()) == 1


def test_source_writer_preserves_legacy_path_when_provided(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    writer = SourceWriter(config)

    result = writer.write(
        SourceWriteRequest(
            source_id="legacy_ai_1",
            title="Legacy AI note",
            body="Migrated body",
            source_type="article",
            domain_hint="ai_agents",
            tags=[],
            source_url="",
            legacy_path="domains/ai/concepts/Legacy AI note.md",
        )
    )

    text = result.path.read_text(encoding="utf-8")
    assert "legacy_path: domains/ai/concepts/Legacy AI note.md" in text
