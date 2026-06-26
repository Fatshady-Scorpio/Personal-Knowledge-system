from pathlib import Path

from personal_knowledge.migration.inventory import collect_markdown_inventory


def test_collect_markdown_inventory_skips_obsidian(tmp_path: Path):
    vault = tmp_path / "vault"
    (vault / ".obsidian").mkdir(parents=True)
    (vault / ".obsidian" / "config.md").write_text("skip", encoding="utf-8")
    (vault / "raw" / "articles").mkdir(parents=True)
    (vault / "raw" / "articles" / "a.md").write_text("# A", encoding="utf-8")

    items = collect_markdown_inventory(vault, ignored_dirs={".obsidian"})

    assert [item.relative_path for item in items] == ["raw/articles/a.md"]
    assert items[0].content_hash
