from pathlib import Path

from personal_knowledge.maintenance.lint import VaultLinter, render_maintenance_markdown


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


def test_render_maintenance_markdown_groups_issues_with_relative_paths(tmp_path: Path):
    vault = tmp_path / "wiki"
    source = vault / "10_sources" / "work_notes" / "note.md"
    concept = vault / "20_knowledge" / "domains" / "ai_agents" / "concepts" / "memory.md"
    source.parent.mkdir(parents=True)
    concept.parent.mkdir(parents=True)
    source.write_text("---\ntype: source\nstatus: raw\nsource_id: note1\n---\n\nBody", encoding="utf-8")
    concept.write_text("---\ntype: knowledge\nsource_refs: []\nstatus: candidate\n---\n\nBody", encoding="utf-8")

    markdown = render_maintenance_markdown(VaultLinter(vault).run(), vault)

    assert "# Knowledge Maintenance Report" in markdown
    assert "- Total issues: 2" in markdown
    assert "## Uncompiled Sources" in markdown
    assert "`10_sources/work_notes/note.md`" in markdown
    assert "## Knowledge Without Source References" in markdown
    assert "`20_knowledge/domains/ai_agents/concepts/memory.md`" in markdown
