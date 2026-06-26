from personal_knowledge.migration.normalize import normalize_markdown


def test_normalizes_concept_frontmatter():
    source = """---
type: concept
tags: ['"AI"']
---

# Transformer

Body
"""
    migrated = normalize_markdown(
        source,
        legacy_path="domains/ai/concepts/Transformer.md",
        target_path="20_knowledge/domains/ai_agents/concepts/Transformer.md",
    )

    assert "type: knowledge" in migrated
    assert "object_type: concept" in migrated
    assert "domain: ai_agents" in migrated
    assert "legacy_path: domains/ai/concepts/Transformer.md" in migrated
    assert "# Transformer" in migrated
    assert "- AI" in migrated


def test_normalizes_source_frontmatter():
    source = "# Raw Article\n\nBody"
    migrated = normalize_markdown(
        source,
        legacy_path="raw/articles/Raw Article.md",
        target_path="10_sources/articles/Raw Article.md",
    )

    assert "type: source" in migrated
    assert "source_type: article" in migrated
    assert "legacy_path: raw/articles/Raw Article.md" in migrated


def test_preserves_source_body_without_frontmatter():
    source = "# Raw Article\n\nBody"
    migrated = normalize_markdown(
        source,
        legacy_path="raw/articles/Raw Article.md",
        target_path="10_sources/articles/Raw Article.md",
    )

    assert migrated.endswith("# Raw Article\n\nBody")


def test_legacy_escaped_tags_are_recovered():
    source = """---
type: concept
tags: ['"\\'Agentic AI\\'"']
---

# Broken Tags

Body
"""
    migrated = normalize_markdown(
        source,
        legacy_path="domains/ai/concepts/Broken Tags.md",
        target_path="20_knowledge/domains/ai_agents/concepts/Broken Tags.md",
    )

    assert "type: knowledge" in migrated
    assert "frontmatter_parse_error:" not in migrated
    assert "- Agentic AI" in migrated
    assert "# Broken Tags" in migrated


def test_legacy_unquoted_colon_title_is_recovered():
    source = """---
type: article
title: Chapter 15: Inter-Agent Communication
source: Agentic Design Patterns
tags: ['Agentic AI']
status: compiled
---

# Chapter Body
"""
    migrated = normalize_markdown(
        source,
        legacy_path="raw/articles/chapter.md",
        target_path="10_sources/articles/chapter.md",
    )

    assert "frontmatter_parse_error:" not in migrated
    assert "title: 'Chapter 15: Inter-Agent Communication'" in migrated
    assert "source_url: Agentic Design Patterns" in migrated
