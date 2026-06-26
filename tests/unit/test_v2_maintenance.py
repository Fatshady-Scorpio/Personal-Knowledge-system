from pathlib import Path

from personal_knowledge.maintenance.lint import VaultLinter


def test_linter_reports_uncompiled_sources(tmp_path: Path):
    vault = tmp_path / "wiki"
    source = vault / "10_sources" / "work_notes" / "note.md"
    source.parent.mkdir(parents=True)
    source.write_text("---\ntype: source\nstatus: raw\nsource_id: note1\n---\n\nBody", encoding="utf-8")

    report = VaultLinter(vault).run()

    assert any(issue.code == "uncompiled_source" and issue.path == source for issue in report.issues)


def test_linter_reports_knowledge_without_source_refs(tmp_path: Path):
    vault = tmp_path / "wiki"
    concept = vault / "20_knowledge" / "domains" / "ai_agents" / "concepts" / "memory.md"
    concept.parent.mkdir(parents=True)
    concept.write_text("---\ntype: knowledge\nsource_refs: []\nstatus: candidate\n---\n\nBody", encoding="utf-8")

    report = VaultLinter(vault).run()

    assert any(issue.code == "missing_source_refs" and issue.path == concept for issue in report.issues)
