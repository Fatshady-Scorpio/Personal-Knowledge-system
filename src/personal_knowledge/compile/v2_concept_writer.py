from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from personal_knowledge.config import VaultConfig
from personal_knowledge.vault.frontmatter import join_frontmatter, split_frontmatter


@dataclass(frozen=True)
class ConceptDraft:
    title: str
    definition: str
    summary: str
    related: list[str] = field(default_factory=list)
    confidence: float = 0.5
    tags: list[str] = field(default_factory=list)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", value.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:80] or "untitled"


class V2ConceptWriter:
    def __init__(self, config: VaultConfig):
        self.config = config

    def write_concepts(self, source_path: Path, concepts: list[ConceptDraft]) -> list[Path]:
        source_meta, source_body = split_frontmatter(source_path.read_text(encoding="utf-8"))
        domain = self.config.normalize_domain(str(source_meta.get("domain_hint") or "personal_systems"))
        created: list[Path] = []

        for concept in concepts:
            output_path = self.config.domains_dir / domain / "concepts" / f"{_slugify(concept.title)}.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(self._build_concept_markdown(concept, source_path, domain), encoding="utf-8")
            created.append(output_path)

        if created:
            source_meta["status"] = "compiled"
            source_path.write_text(join_frontmatter(source_meta, source_body), encoding="utf-8")

        return created

    def _build_concept_markdown(self, concept: ConceptDraft, source_path: Path, domain: str) -> str:
        related_links = [f"[[{item}]]" for item in concept.related]
        frontmatter: dict[str, Any] = {
            "type": "knowledge",
            "object_type": "concept",
            "domain": domain,
            "title": concept.title,
            "aliases": [],
            "source_refs": [str(source_path)],
            "tags": concept.tags,
            "status": "candidate",
            "confidence": concept.confidence,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "reviewed_at": None,
        }
        body = "\n".join(
            [
                f"# {concept.title}",
                "",
                "## Definition",
                "",
                concept.definition,
                "",
                "## Summary",
                "",
                concept.summary,
                "",
                "## Related",
                "",
                "\n".join(f"- {link}" for link in related_links) if related_links else "",
                "",
            ]
        )
        return join_frontmatter(frontmatter, body)
