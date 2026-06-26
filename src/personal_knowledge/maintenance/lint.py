from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from personal_knowledge.vault.frontmatter import split_frontmatter

ISSUE_TITLES = {
    "uncompiled_source": "Uncompiled Sources",
    "missing_source_refs": "Knowledge Without Source References",
}

ISSUE_ACTIONS = {
    "uncompiled_source": "Compile or explicitly archive the source.",
    "missing_source_refs": "Add source_refs or mark the page as Sam synthesis with review notes.",
}


@dataclass(frozen=True)
class VaultIssue:
    code: str
    path: Path
    message: str


@dataclass(frozen=True)
class VaultLintReport:
    issues: list[VaultIssue]

    def counts_by_code(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for issue in self.issues:
            counts[issue.code] = counts.get(issue.code, 0) + 1
        return counts


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


def render_maintenance_markdown(report: VaultLintReport, vault_root: Path) -> str:
    generated_at = datetime.now().isoformat(timespec="seconds")
    counts = report.counts_by_code()
    lines = [
        "# Knowledge Maintenance Report",
        "",
        f"- Generated at: {generated_at}",
        f"- Vault: {vault_root}",
        f"- Total issues: {len(report.issues)}",
        "",
        "## Summary",
        "",
    ]

    if not counts:
        lines.extend(["No maintenance issues found.", ""])
    else:
        for code, count in sorted(counts.items()):
            title = ISSUE_TITLES.get(code, code)
            lines.append(f"- {title}: {count}")
        lines.append("")

    grouped: dict[str, list[VaultIssue]] = {}
    for issue in report.issues:
        grouped.setdefault(issue.code, []).append(issue)

    for code, issues in sorted(grouped.items()):
        title = ISSUE_TITLES.get(code, code)
        action = ISSUE_ACTIONS.get(code, "Review and decide the next action.")
        lines.extend([f"## {title}", "", f"Recommended action: {action}", ""])
        for issue in issues:
            try:
                display_path = issue.path.relative_to(vault_root)
            except ValueError:
                display_path = issue.path
            lines.append(f"- `{display_path}` - {issue.message}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
