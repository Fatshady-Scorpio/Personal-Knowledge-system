from __future__ import annotations

import re
from typing import Any

import yaml
from yaml import YAMLError


def _recover_legacy_flow_list(raw: str, key: str) -> list[str] | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(raw)
    if match is None:
        return None
    value = match.group(1).strip()
    if not value.startswith("[") or not value.endswith("]"):
        return [value] if value else []
    inner = value[1:-1].strip()
    if inner == "":
        return []
    return [part.strip() for part in inner.split(",") if part.strip()]


def _clean_legacy_scalar(value: str) -> str:
    text = value.strip()
    previous = None
    while previous != text:
        previous = text
        text = text.replace("\\'", "'").replace('\\"', '"')
        text = text.strip().strip("'").strip('"').strip()
    return text


def _recover_legacy_scalars(raw: str) -> dict[str, str]:
    recovered: dict[str, str] = {}
    for key in ["type", "title", "source", "source_id", "domain", "status", "created_at", "collected_at", "confidence"]:
        match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, flags=re.MULTILINE)
        if match is not None:
            recovered[key] = _clean_legacy_scalar(match.group(1))
    return recovered


def _safe_load_frontmatter(raw: str) -> dict[str, Any]:
    try:
        parsed = yaml.safe_load(raw) or {}
        return parsed if isinstance(parsed, dict) else {}
    except YAMLError as first_error:
        recovered: dict[str, Any] = {}
        sanitized = raw
        for key in ["tags", "related_topics"]:
            values = _recover_legacy_flow_list(raw, key)
            if values is None:
                continue
            recovered[key] = values
            sanitized = re.sub(rf"^{re.escape(key)}:\s*.+$", f"{key}: []", sanitized, flags=re.MULTILINE)

        recovered.update(_recover_legacy_scalars(raw))

        if not recovered:
            return {"frontmatter_parse_error": str(first_error), "legacy_frontmatter_raw": raw}

        try:
            parsed = yaml.safe_load(sanitized) or {}
        except YAMLError as second_error:
            return {"frontmatter_recovered": True, **recovered}

        if not isinstance(parsed, dict):
            parsed = {}
        parsed.update(recovered)
        return parsed


def split_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown
    end = markdown.find("\n---", 4)
    if end == -1:
        return {}, markdown
    raw = markdown[4:end]
    body = markdown[end + 4 :].lstrip("\n")
    return _safe_load_frontmatter(raw), body


def join_frontmatter(frontmatter: dict[str, Any], body: str) -> str:
    raw = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{raw}\n---\n\n{body.lstrip()}"
