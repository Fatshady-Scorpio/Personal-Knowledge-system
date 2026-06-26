from __future__ import annotations

import hashlib
from datetime import date
from pathlib import PurePosixPath
from typing import Any

from personal_knowledge.vault.frontmatter import join_frontmatter, split_frontmatter


def _clean_scalar(value: Any) -> str:
    text = str(value).strip()
    previous = None
    while previous != text:
        previous = text
        text = text.replace("\\'", "'").replace('\\"', '"')
        text = text.strip().strip("'").strip('"').strip()
    return text


def _clean_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        values = [str(value)]

    tags: list[str] = []
    seen: set[str] = set()
    for item in values:
        cleaned = _clean_scalar(item)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        tags.append(cleaned)
    return tags


def _domain_from_target(target_path: str) -> str:
    parts = PurePosixPath(target_path).parts
    if len(parts) >= 4 and parts[0] == "20_knowledge" and parts[1] == "domains":
        return parts[2]
    return "personal_systems"


def _object_type_from_target(target_path: str) -> str:
    parts = PurePosixPath(target_path).parts
    if "concepts" in parts:
        return "concept"
    if "maps" in parts:
        return "map"
    if "principles" in parts:
        return "principle"
    if "cases" in parts:
        return "case"
    if "playbooks" in parts:
        return "playbook"
    if "questions" in parts:
        return "question"
    return "concept"


def _source_type_from_target(target_path: str) -> str:
    parts = PurePosixPath(target_path).parts
    if len(parts) >= 2 and parts[0] == "10_sources":
        return {
            "articles": "article",
            "papers": "paper",
            "books": "book",
            "videos": "video",
            "conversations": "conversation",
            "research_reports": "research_report",
            "work_notes": "work_note",
            "clippings": "clipping",
        }.get(parts[1], "source")
    return "source"


def normalize_markdown(markdown: str, legacy_path: str, target_path: str) -> str:
    old, body = split_frontmatter(markdown)
    today = date.today().isoformat()

    if target_path.startswith("20_knowledge/"):
        source_refs = []
        if old.get("created_from"):
            source_refs.append(str(old["created_from"]))
        fm = {
            "type": "knowledge",
            "object_type": _object_type_from_target(target_path),
            "domain": _domain_from_target(target_path),
            "title": old.get("title"),
            "aliases": old.get("aliases", []),
            "source_refs": source_refs,
            "tags": _clean_tags(old.get("tags")),
            "status": old.get("review_status", "candidate"),
            "confidence": old.get("confidence"),
            "created_at": str(old.get("created_at", today)),
            "updated_at": today,
            "reviewed_at": old.get("reviewed_at"),
            "legacy_path": legacy_path,
        }
        if old.get("frontmatter_parse_error"):
            fm["frontmatter_parse_error"] = old["frontmatter_parse_error"]
            fm["legacy_frontmatter_raw"] = old.get("legacy_frontmatter_raw", "")
        return join_frontmatter(fm, body)

    if target_path.startswith("10_sources/"):
        content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        fm = {
            "type": "source",
            "source_type": _source_type_from_target(target_path),
            "title": old.get("title"),
            "source_url": old.get("source", ""),
            "source_id": old.get("source_id", ""),
            "domain_hint": old.get("domain", ""),
            "tags": _clean_tags(old.get("tags")),
            "status": old.get("status", "raw"),
            "content_hash": old.get("content_hash", content_hash),
            "collected_at": str(old.get("collected_at", today)),
            "legacy_path": legacy_path,
        }
        if old.get("frontmatter_parse_error"):
            fm["frontmatter_parse_error"] = old["frontmatter_parse_error"]
            fm["legacy_frontmatter_raw"] = old.get("legacy_frontmatter_raw", "")
        return join_frontmatter(fm, body)

    old["legacy_path"] = legacy_path
    if "tags" in old:
        old["tags"] = _clean_tags(old["tags"])
    return join_frontmatter(old, body)
