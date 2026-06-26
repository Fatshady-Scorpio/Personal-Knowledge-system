import json
from pathlib import Path

from personal_knowledge.compile import ConceptDraft
from personal_knowledge.compile.v2_source_compiler import SourceDocument, V2SourceCompiler
from personal_knowledge.config import VaultConfig
from personal_knowledge.ingest import SourceWriteRequest, SourceWriter
from personal_knowledge.retrieve import V2IndexManager


class FakeExtractor:
    def __init__(self):
        self.seen: list[SourceDocument] = []

    def extract(self, source: SourceDocument) -> list[ConceptDraft]:
        self.seen.append(source)
        return [
            ConceptDraft(
                title="分层记忆系统",
                definition="将记忆按生命周期分层。",
                summary="短期记忆、工作记忆和长期记忆服务不同任务。",
                related=["上下文压缩"],
                confidence=0.9,
                tags=["Agent"],
            )
        ]


def test_v2_source_compiler_extracts_writes_indexes_and_logs(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    source_result = SourceWriter(config).write(
        SourceWriteRequest(
            source_id="source_1",
            title="Agent Memory",
            body="# Agent Memory\n\nMemory hierarchy",
            source_type="article",
            domain_hint="ai",
        )
    )
    extractor = FakeExtractor()

    result = V2SourceCompiler(config=config, extractor=extractor).compile(source_result.path)

    assert result.status == "compiled"
    assert result.domain == "ai_agents"
    assert result.created_paths == [config.domains_dir / "ai_agents" / "concepts" / "分层记忆系统.md"]
    assert extractor.seen[0].title == "Agent Memory"
    assert V2IndexManager(config).get_index("ai_agents").search("分层记忆", top_k=1)[0]["name"] == "分层记忆系统"

    operations = [json.loads(line) for line in config.operation_log_path.read_text(encoding="utf-8").splitlines()]
    assert operations[-1]["event"] == "source_compiled"
    assert operations[-1]["created_count"] == 1


def test_v2_source_compiler_skips_compiled_source_without_force(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    source_result = SourceWriter(config).write(
        SourceWriteRequest(
            source_id="source_1",
            title="Agent Memory",
            body="# Agent Memory\n\nMemory hierarchy",
            source_type="article",
            domain_hint="ai",
        )
    )
    compiler = V2SourceCompiler(config=config, extractor=FakeExtractor())
    compiler.compile(source_result.path)

    second = compiler.compile(source_result.path)

    assert second.status == "skipped_compiled"
    assert second.created_paths == []
