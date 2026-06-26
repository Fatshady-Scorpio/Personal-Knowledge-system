from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from personal_knowledge.config import VaultConfig
from personal_knowledge.vault.frontmatter import join_frontmatter


SOURCE_TYPE_DIRS = {
    "article": "articles",
    "paper": "papers",
    "book": "books",
    "video": "videos",
    "conversation": "conversations",
    "research_report": "research_reports",
    "work_note": "work_notes",
    "clipping": "clippings",
}


@dataclass(frozen=True)
class SourceWriteRequest:
    source_id: str
    title: str
    body: str
    source_type: str
    domain_hint: str = "personal_systems"
    source_url: str = ""
    tags: list[str] = field(default_factory=list)
    collected_at: str | None = None
    legacy_path: str = ""


@dataclass(frozen=True)
class SourceWriteResult:
    status: str
    path: Path
    source_id: str
    content_hash: str


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]+", "_", value.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned[:80] or "untitled"


def _json_default(value: Any) -> str:
    if isinstance(value, Path):
        return str(value)
    return str(value)


class SourceWriter:
    def __init__(self, config: VaultConfig):
        self.config = config

    def write(self, request: SourceWriteRequest) -> SourceWriteResult:
        content_hash = hashlib.sha256(request.body.encode("utf-8")).hexdigest()
        existing = self._find_by_hash(content_hash)
        if existing is not None:
            path = Path(existing["path"])
            self._append_operation("source_duplicate", request, path, content_hash)
            return SourceWriteResult("duplicate", path, request.source_id, content_hash)

        source_dir = self.config.sources_dir / SOURCE_TYPE_DIRS.get(request.source_type, "work_notes")
        source_dir.mkdir(parents=True, exist_ok=True)
        path = source_dir / f"{_slugify(request.title)}-{_slugify(request.source_id)}.md"
        path.write_text(self._build_markdown(request, content_hash), encoding="utf-8")
        self._append_manifest(request, path, content_hash)
        self._append_operation("source_created", request, path, content_hash)
        return SourceWriteResult("created", path, request.source_id, content_hash)

    def _build_markdown(self, request: SourceWriteRequest, content_hash: str) -> str:
        frontmatter = {
            "type": "source",
            "source_type": request.source_type,
            "title": request.title,
            "source_url": request.source_url,
            "source_id": request.source_id,
            "domain_hint": self.config.normalize_domain(request.domain_hint),
            "tags": request.tags,
            "status": "raw",
            "content_hash": content_hash,
            "collected_at": request.collected_at or datetime.now().isoformat(timespec="seconds"),
        }
        if request.legacy_path:
            frontmatter["legacy_path"] = request.legacy_path
        return join_frontmatter(frontmatter, request.body)

    def _load_manifest(self) -> list[dict[str, Any]]:
        path = self.config.knowledge_manifest_path
        if not path.exists():
            return []
        entries = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entries.append(json.loads(line))
        return entries

    def _find_by_hash(self, content_hash: str) -> dict[str, Any] | None:
        for entry in self._load_manifest():
            if entry.get("content_hash") == content_hash:
                return entry
        return None

    def _append_manifest(self, request: SourceWriteRequest, path: Path, content_hash: str) -> None:
        manifest_path = self.config.knowledge_manifest_path
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "source_id": request.source_id,
            "source_type": request.source_type,
            "title": request.title,
            "path": str(path),
            "content_hash": content_hash,
            "domain_hint": self.config.normalize_domain(request.domain_hint),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        with manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _append_operation(self, event: str, request: SourceWriteRequest, path: Path, content_hash: str) -> None:
        operation_path = self.config.operation_log_path
        operation_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "event": event,
            "source_id": request.source_id,
            "source_type": request.source_type,
            "path": str(path),
            "content_hash": content_hash,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "request": asdict(request),
        }
        with operation_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, default=_json_default) + "\n")
