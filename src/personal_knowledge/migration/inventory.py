from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InventoryItem:
    absolute_path: Path
    relative_path: str
    content_hash: str
    size_bytes: int


def _is_ignored(path: Path, root: Path, ignored_dirs: set[str]) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in ignored_dirs for part in rel_parts)


def collect_markdown_inventory(root: Path, ignored_dirs: set[str]) -> list[InventoryItem]:
    items: list[InventoryItem] = []
    for path in sorted(root.rglob("*.md")):
        if _is_ignored(path, root, ignored_dirs):
            continue
        data = path.read_bytes()
        items.append(
            InventoryItem(
                absolute_path=path,
                relative_path=path.relative_to(root).as_posix(),
                content_hash=hashlib.sha256(data).hexdigest(),
                size_bytes=len(data),
            )
        )
    return items
