from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from personal_knowledge.vault.frontmatter import split_frontmatter


@dataclass(frozen=True)
class VaultIssue:
    code: str
    path: Path
    message: str


@dataclass(frozen=True)
class VaultLintReport:
    issues: list[VaultIssue]


class VaultLinter:
    def __init__(self, vault_root: Path):
        self.vault_root = vault_root

    def run(self) -> VaultLintReport:
        issues: list[VaultIssue] = []
        issues.extend(self._uncompiled_sources())
        issues.extend(self._knowledge_without_sources())
        return VaultLintReport(issues=issues)

    def _uncompiled_sources(self) -> list[VaultIssue]:
        issues: list[VaultIssue] = []
        for path in sorted((self.vault_root / "10_sources").glob("**/*.md")):
            metadata, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            if metadata.get("type") == "source" and metadata.get("status") == "raw":
                issues.append(VaultIssue("uncompiled_source", path, "Source has not been compiled."))
        return issues

    def _knowledge_without_sources(self) -> list[VaultIssue]:
        issues: list[VaultIssue] = []
        for path in sorted((self.vault_root / "20_knowledge").glob("**/*.md")):
            metadata, _ = split_frontmatter(path.read_text(encoding="utf-8"))
            if metadata.get("type") == "knowledge" and not metadata.get("source_refs"):
                issues.append(VaultIssue("missing_source_refs", path, "Knowledge page has no source references."))
        return issues
