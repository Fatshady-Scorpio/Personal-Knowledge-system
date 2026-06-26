# Knowledge V2 Data First Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild Sam's Personal Knowledge system around the migrated Obsidian vault data, ignoring legacy code compatibility while preserving old data traceability.

**Architecture:** Treat `/Users/samcao/Obsidian/wiki` as the product and source of truth. Keep the local Python project as a small engine for ingestion, compilation, retrieval, and maintenance. Keep Command Center as orchestration only, with all local vault writes going through the Local Knowledge Runner.

**Tech Stack:** Python 3.12, pytest, Obsidian Markdown, YAML frontmatter, per-domain BM25 indexes, TypeScript Command Center task contracts, Local Runner process execution.

---

## File Structure

### Personal Knowledge Project

- Modify: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/config/vault.yaml`
  - Responsibility: declare canonical vault path, valid domains, source types, and safe write roots.
- Modify: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/src/personal_knowledge/ingest/source_writer.py`
  - Responsibility: idempotently write source files into `10_sources`.
- Modify: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/src/personal_knowledge/compile/v2_source_compiler.py`
  - Responsibility: compile one source into maintained knowledge pages.
- Modify: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/src/personal_knowledge/retrieve/v2_indexer.py`
  - Responsibility: build/search per-domain indexes from `20_knowledge`.
- Create: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/src/personal_knowledge/maintenance/lint.py`
  - Responsibility: produce reviewable maintenance findings for orphan, duplicate, stale, uncompiled, and missing-source issues.
- Create: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/scripts/maintain_v2.py`
  - Responsibility: CLI entrypoint for maintenance reports.
- Test: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/tests/unit/test_v2_maintenance.py`

### Command Center

- Modify: `/Users/samcao/Documents/personal system/apps/local-runner/src/knowledgeRunner.ts`
  - Responsibility: call v2 ingest, compile, and index scripts and return a deposit report.
- Modify: `/Users/samcao/Documents/personal system/apps/local-runner/test/knowledgeRunner.test.ts`
  - Responsibility: cover success, duplicate-source skip, compile failure, and index failure cases.
- Modify: `/Users/samcao/Documents/personal system/apps/command-center/src/server/services/secretaryDecisionExecutor.ts`
  - Responsibility: route explicit knowledge-deposit requests to `knowledge_deposit`.
- Modify: `/Users/samcao/Documents/personal system/apps/command-center/test/secretaryDecisionExecutor.test.ts`
  - Responsibility: ensure ambiguous capture/research/deposit requests ask for clarification instead of guessing.

## Task 1: Lock The V2 Contract

**Files:**

- Modify: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/config/vault.yaml`
- Test: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/tests/unit/test_v2_config.py`

- [ ] **Step 1: Add contract assertions to config tests**

Add assertions to `test_v2_config.py`:

```python
from personal_knowledge.ingest.source_writer import SOURCE_TYPE_DIRS


def test_vault_config_uses_canonical_obsidian_vault():
    config = load_vault_config(Path("config/vault.yaml"))
    assert str(config.vault_root) == "/Users/samcao/Obsidian/wiki"
    assert config.domain_map["ai"] == "ai_agents"
    assert config.domain_map["general"] == "personal_systems"
    assert "research_report" in SOURCE_TYPE_DIRS
    assert "work_note" in SOURCE_TYPE_DIRS
```

- [ ] **Step 2: Run the focused test and confirm failure if fields are missing**

Run:

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src pytest tests/unit/test_v2_config.py -q
```

Expected before implementation if any field is missing: assertion failure naming the missing contract field.

- [ ] **Step 3: Update `config/vault.yaml`**

Ensure the file contains these values:

```yaml
current_vault: /Users/samcao/Obsidian/wiki
staging_vault: /Users/samcao/Obsidian/wiki-v2-staging
project_root: /Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system
domains:
  ai: ai_agents
  product: product_growth
  investment: business_investment
  general: personal_systems
```

- [ ] **Step 4: Run the focused test again**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_v2_config.py -q
```

Expected: all tests pass.

## Task 2: Keep Ingestion Data-First And Duplicate-Safe

**Files:**

- Modify: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/src/personal_knowledge/ingest/source_writer.py`
- Test: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/tests/unit/test_source_writer.py`

- [ ] **Step 1: Add duplicate and legacy traceability tests**

Add tests:

```python
def test_source_writer_skips_same_content_hash(tmp_path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    writer = SourceWriter(config)
    request = SourceWriteRequest(
        source_id="task_1",
        title="Agent memory note",
        body="Stable knowledge belongs in Obsidian.",
        source_type="work_note",
        domain_hint="ai_agents",
        tags=["agent"],
        source_url="",
    )

    first = writer.write(request)
    second = writer.write(request)

    assert first.content_hash == second.content_hash
    assert second.status == "duplicate"
    assert first.path == second.path


def test_source_writer_preserves_legacy_path_when_provided(tmp_path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    writer = SourceWriter(config)
    result = writer.write(
        SourceWriteRequest(
            source_id="legacy_ai_1",
            title="Legacy AI note",
            body="Migrated body",
            source_type="article",
            domain_hint="ai_agents",
            tags=[],
            source_url="",
            legacy_path="domains/ai/concepts/Legacy AI note.md",
        )
    )

    text = result.path.read_text(encoding="utf-8")
    assert "legacy_path: domains/ai/concepts/Legacy AI note.md" in text
```

- [ ] **Step 2: Run focused tests**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_source_writer.py -q
```

Expected before implementation if behavior is missing: one or both tests fail.

- [ ] **Step 3: Implement minimal writer behavior**

Implement these rules in `SourceWriter.write`:

```python
content_hash = sha256(request.body.encode("utf-8")).hexdigest()
existing_path = self._find_by_hash(content_hash)
if existing_path is not None:
    path = Path(existing_path["path"])
    return SourceWriteResult(status="duplicate", path=path, source_id=request.source_id, content_hash=content_hash)
```

Extend `SourceWriteRequest` with `legacy_path: str = ""`. When rendering frontmatter, include `legacy_path` only when request data provides it.

- [ ] **Step 4: Run focused tests again**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_source_writer.py -q
```

Expected: all tests pass.

## Task 3: Add Reviewable Maintenance Reports

**Files:**

- Create: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/src/personal_knowledge/maintenance/lint.py`
- Create: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/scripts/maintain_v2.py`
- Test: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/tests/unit/test_v2_maintenance.py`

- [ ] **Step 1: Write maintenance tests**

Create `test_v2_maintenance.py`:

```python
from pathlib import Path

from personal_knowledge.maintenance.lint import VaultLinter


def test_linter_reports_uncompiled_sources(tmp_path: Path):
    vault = tmp_path / "wiki"
    source = vault / "10_sources" / "work_notes" / "note.md"
    source.parent.mkdir(parents=True)
    source.write_text("---\ntype: source\nstatus: raw\nsource_id: note1\n---\n\nBody", encoding="utf-8")

    report = VaultLinter(vault).run()

    assert any(issue.code == "uncompiled_source" and issue.path == source for issue in report.issues)


def test_linter_reports_knowledge_without_source_refs(tmp_path: Path):
    vault = tmp_path / "wiki"
    concept = vault / "20_knowledge" / "domains" / "ai_agents" / "concepts" / "memory.md"
    concept.parent.mkdir(parents=True)
    concept.write_text("---\ntype: knowledge\nsource_refs: []\nstatus: candidate\n---\n\nBody", encoding="utf-8")

    report = VaultLinter(vault).run()

    assert any(issue.code == "missing_source_refs" and issue.path == concept for issue in report.issues)
```

- [ ] **Step 2: Run focused maintenance tests**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_v2_maintenance.py -q
```

Expected before implementation: import failure for `personal_knowledge.maintenance.lint`.

- [ ] **Step 3: Implement linter data types and checks**

Create `lint.py` with:

```python
from dataclasses import dataclass
from pathlib import Path

from personal_knowledge.vault.frontmatter import parse_frontmatter


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
        for path in (self.vault_root / "10_sources").glob("**/*.md"):
            metadata, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            if metadata.get("status") == "raw":
                issues.append(VaultIssue("uncompiled_source", path, "Source has not been compiled."))
        return issues

    def _knowledge_without_sources(self) -> list[VaultIssue]:
        issues: list[VaultIssue] = []
        for path in (self.vault_root / "20_knowledge").glob("**/*.md"):
            metadata, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
            if metadata.get("type") == "knowledge" and not metadata.get("source_refs"):
                issues.append(VaultIssue("missing_source_refs", path, "Knowledge page has no source references."))
        return issues
```

- [ ] **Step 4: Add CLI**

Create `scripts/maintain_v2.py`:

```python
#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from pathlib import Path

from personal_knowledge.config import load_vault_config
from personal_knowledge.maintenance.lint import VaultLinter


def main() -> None:
    parser = argparse.ArgumentParser(description="Run V2 vault maintenance checks")
    parser.add_argument("--config", default="config/vault.yaml")
    args = parser.parse_args()

    config = load_vault_config(Path(args.config))
    report = VaultLinter(config.vault_root).run()
    print(json.dumps({"issues": [issue.__dict__ | {"path": str(issue.path)} for issue in report.issues]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run maintenance tests again**

Run:

```bash
PYTHONPATH=src pytest tests/unit/test_v2_maintenance.py -q
```

Expected: all tests pass.

## Task 4: Harden Local Knowledge Runner Reporting

**Files:**

- Modify: `/Users/samcao/Documents/personal system/apps/local-runner/src/knowledgeRunner.ts`
- Modify: `/Users/samcao/Documents/personal system/apps/local-runner/test/knowledgeRunner.test.ts`

- [ ] **Step 1: Add local runner failure tests**

Add tests that simulate:

```ts
it("stops before compile when ingest fails", async () => {
  const calls: string[][] = [];
  const runCommand: RunKnowledgeCommand = async (_command, args) => {
    calls.push(args);
    return { exitCode: 1, stdout: "", stderr: "ingest failed" };
  };

  const result = await runKnowledgeDeposit(makeInput(), runCommand);

  expect(result.exitCode).toBe(1);
  expect(calls).toHaveLength(1);
  expect(result.stdout).toContain("ingest_source.py");
  expect(result.stdout).toContain("ingest failed");
});

it("reports index failure after successful compile", async () => {
  const runCommand: RunKnowledgeCommand = async (_command, args) => {
    if (args[0] === "scripts/ingest_source.py") {
      return { exitCode: 0, stdout: JSON.stringify({ path: "/Users/samcao/Obsidian/wiki/10_sources/work_notes/a.md" }), stderr: "" };
    }
    if (args[0] === "scripts/search_v2.py") {
      return { exitCode: 1, stdout: "", stderr: "index failed" };
    }
    return { exitCode: 0, stdout: "compiled", stderr: "" };
  };

  const result = await runKnowledgeDeposit(makeInput(), runCommand);

  expect(result.exitCode).toBe(1);
  expect(result.stdout).toContain("compile_source.py");
  expect(result.stdout).toContain("index failed");
});
```

- [ ] **Step 2: Run local runner tests**

Run:

```bash
cd "/Users/samcao/Documents/personal system"
pnpm --filter @personal-system/local-runner test -- knowledgeRunner
```

Expected before implementation if reporting is incomplete: failure assertions on stdout content.

- [ ] **Step 3: Ensure stderr is included in step logs**

Confirm `formatStepLog` includes both stdout and stderr:

```ts
function formatStepLog(label: string, result: CodexRunResult): string {
  return [
    `## ${label}`,
    "",
    `exitCode: ${result.exitCode}`,
    "",
    "stdout:",
    result.stdout.trim() || "(empty)",
    "",
    "stderr:",
    result.stderr.trim() || "(empty)"
  ].join("\n");
}
```

- [ ] **Step 4: Run local runner tests again**

Run:

```bash
pnpm --filter @personal-system/local-runner test -- knowledgeRunner
```

Expected: all `knowledgeRunner` tests pass.

## Task 5: Prevent Secretary Context Pollution For Deposit Intent

**Files:**

- Modify: `/Users/samcao/Documents/personal system/apps/command-center/src/server/services/secretaryDecisionExecutor.ts`
- Modify: `/Users/samcao/Documents/personal system/apps/command-center/test/secretaryDecisionExecutor.test.ts`

- [ ] **Step 1: Add intent isolation tests**

Add tests:

```ts
it("asks for clarification when a new request could be research or deposit", async () => {
  const result = await executeSecretaryDecision({
    text: "帮我整理一下今天看到的 AI 信息，后面沉淀到知识库",
    threadContext: { previousTaskScenario: "knowledge_deposit" }
  });

  expect(result.type).toBe("clarification");
  expect(result.message).toContain("你是要我先研究，还是把已有内容沉淀到知识库");
});

it("creates a knowledge deposit only when source body or artifact is present", async () => {
  const result = await executeSecretaryDecision({
    text: "把这份研究报告沉淀到知识库",
    artifact: { title: "Agent memory report", markdown: "# Report\n\nBody" }
  });

  expect(result.type).toBe("task_created");
  expect(result.task.scenario).toBe("knowledge_deposit");
});
```

- [ ] **Step 2: Run focused command-center tests**

Run:

```bash
cd "/Users/samcao/Documents/personal system"
pnpm --filter @personal-system/command-center test -- secretaryDecisionExecutor
```

Expected before implementation if context pollution remains: first test creates the wrong task or gives an overconfident answer.

- [ ] **Step 3: Implement explicit routing guard**

Implement a guard with these rules:

```ts
const hasDepositArtifact = artifact?.markdown?.trim() || artifact?.url?.trim();
const asksToDeposit = /沉淀|保存到知识库|写入知识库|归档到知识库/.test(text);
const asksToResearch = /研究|调研|查一下|整理信息|生成报告/.test(text);

if (asksToDeposit && asksToResearch && !hasDepositArtifact) {
  return {
    type: "clarification",
    message: "你是要我先研究并生成内容，还是把已有内容沉淀到知识库？如果是沉淀，请发我具体内容或报告链接。"
  };
}

if (asksToDeposit && hasDepositArtifact) {
  return createKnowledgeDepositTask(artifact);
}
```

- [ ] **Step 4: Run focused command-center tests again**

Run:

```bash
pnpm --filter @personal-system/command-center test -- secretaryDecisionExecutor
```

Expected: focused tests pass.

## Task 6: End-To-End Smoke

**Files:**

- Read: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/scripts/ingest_source.py`
- Read: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/scripts/compile_source.py`
- Read: `/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor/scripts/search_v2.py`

- [ ] **Step 1: Run Personal Knowledge unit tests**

Run:

```bash
cd "/Users/samcao/Documents/Documents/personal_projects/Personal Knowledge system/.worktrees/knowledge-v2-refactor"
PYTHONPATH=src pytest tests/unit -q
```

Expected: all tests pass.

- [ ] **Step 2: Run search smoke**

Run:

```bash
PYTHONPATH=src python scripts/search_v2.py Agent 记忆 --domain ai_agents --top-k 5 --config config/vault.yaml
```

Expected: at least one result under `/Users/samcao/Obsidian/wiki/20_knowledge/domains/ai_agents/`.

- [ ] **Step 3: Run Command Center local runner test**

Run:

```bash
cd "/Users/samcao/Documents/personal system"
pnpm --filter @personal-system/local-runner test -- knowledgeRunner
```

Expected: all `knowledgeRunner` tests pass.

- [ ] **Step 4: Run Command Center secretary routing test**

Run:

```bash
pnpm --filter @personal-system/command-center test -- secretaryDecisionExecutor
```

Expected: secretary creates deposit tasks only when source content or artifact is present, and asks clarification for mixed new requests.
