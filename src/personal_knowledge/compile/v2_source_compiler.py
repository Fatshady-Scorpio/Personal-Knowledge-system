from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol

from personal_knowledge.compile.v2_concept_writer import ConceptDraft, V2ConceptWriter
from personal_knowledge.config import VaultConfig
from personal_knowledge.retrieve import V2IndexManager
from personal_knowledge.vault.frontmatter import split_frontmatter


@dataclass(frozen=True)
class SourceDocument:
    path: Path
    title: str
    body: str
    source_type: str
    domain_hint: str
    tags: list[str]
    metadata: dict


class ConceptExtractor(Protocol):
    def extract(self, source: SourceDocument) -> list[ConceptDraft]:
        ...


@dataclass(frozen=True)
class CompileSourceResult:
    status: str
    source_path: Path
    domain: str
    created_paths: list[Path]
    indexed_count: int


class V2SourceCompiler:
    def __init__(self, config: VaultConfig, extractor: ConceptExtractor):
        self.config = config
        self.extractor = extractor

    def compile(self, source_path: Path, force: bool = False) -> CompileSourceResult:
        source = self._read_source(source_path)
        domain = self.config.normalize_domain(source.domain_hint)

        if source.metadata.get("status") == "compiled" and not force:
            return CompileSourceResult("skipped_compiled", source_path, domain, [], 0)

        concepts = self.extractor.extract(source)
        created_paths = V2ConceptWriter(self.config).write_concepts(source_path, concepts)
        indexed_count = V2IndexManager(self.config).build_domain(domain) if created_paths else 0
        self._append_operation("source_compiled", source, domain, created_paths, indexed_count)
        return CompileSourceResult("compiled", source_path, domain, created_paths, indexed_count)

    def _read_source(self, source_path: Path) -> SourceDocument:
        metadata, body = split_frontmatter(source_path.read_text(encoding="utf-8"))
        tags = metadata.get("tags") or []
        if not isinstance(tags, list):
            tags = [str(tags)]
        return SourceDocument(
            path=source_path,
            title=str(metadata.get("title") or source_path.stem),
            body=body,
            source_type=str(metadata.get("source_type") or "source"),
            domain_hint=str(metadata.get("domain_hint") or "personal_systems"),
            tags=[str(tag) for tag in tags],
            metadata=metadata,
        )

    def _append_operation(
        self,
        event: str,
        source: SourceDocument,
        domain: str,
        created_paths: list[Path],
        indexed_count: int,
    ) -> None:
        path = self.config.operation_log_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "event": event,
            "source_path": str(source.path),
            "domain": domain,
            "created_paths": [str(item) for item in created_paths],
            "created_count": len(created_paths),
            "indexed_count": indexed_count,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
