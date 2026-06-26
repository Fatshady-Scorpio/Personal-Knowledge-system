from pathlib import Path

from personal_knowledge.compile.v2_concept_writer import ConceptDraft, V2ConceptWriter
from personal_knowledge.config import VaultConfig
from personal_knowledge.ingest import SourceWriteRequest, SourceWriter


def test_v2_concept_writer_writes_concepts_and_marks_source_compiled(tmp_path: Path):
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

    created = V2ConceptWriter(config).write_concepts(
        source_path=source_result.path,
        concepts=[
            ConceptDraft(
                title="分层记忆系统",
                definition="将记忆按生命周期分层。",
                summary="短期记忆、工作记忆和长期记忆服务不同任务。",
                related=["上下文压缩"],
                confidence=0.9,
                tags=["Agent"],
            )
        ],
    )

    assert created == [config.domains_dir / "ai_agents" / "concepts" / "分层记忆系统.md"]
    text = created[0].read_text(encoding="utf-8")
    assert "type: knowledge" in text
    assert "object_type: concept" in text
    assert "source_refs:" in text
    assert "[[上下文压缩]]" in text
    assert "status: compiled" in source_result.path.read_text(encoding="utf-8")
