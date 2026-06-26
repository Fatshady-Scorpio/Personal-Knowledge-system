import json
from pathlib import Path

from personal_knowledge.compile.extractors import JsonFileConceptExtractor, LLMConceptExtractor, parse_concept_drafts
from personal_knowledge.compile.v2_source_compiler import SourceDocument


def test_parse_concept_drafts_from_fenced_json():
    response = """```json
[
  {
    "title": "分层记忆系统",
    "definition": "将记忆按生命周期分层。",
    "summary": "短期和长期记忆承担不同任务。",
    "related": ["上下文压缩"],
    "confidence": 0.9,
    "tags": ["Agent"]
  }
]
```"""

    concepts = parse_concept_drafts(response)

    assert concepts[0].title == "分层记忆系统"
    assert concepts[0].related == ["上下文压缩"]
    assert concepts[0].confidence == 0.9


def test_json_file_concept_extractor_reads_concepts(tmp_path: Path):
    concept_path = tmp_path / "concepts.json"
    concept_path.write_text(
        json.dumps(
            [
                {
                    "title": "分层记忆系统",
                    "definition": "将记忆按生命周期分层。",
                    "summary": "短期和长期记忆承担不同任务。",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    source = SourceDocument(
        path=tmp_path / "source.md",
        title="Source",
        body="Body",
        source_type="article",
        domain_hint="ai_agents",
        tags=[],
        metadata={},
    )

    concepts = JsonFileConceptExtractor(concept_path).extract(source)

    assert concepts[0].title == "分层记忆系统"


def test_llm_concept_extractor_uses_injected_v2_chat_client(tmp_path: Path):
    class FakeChatClient:
        def __init__(self):
            self.calls = []

        def call(self, **kwargs):
            self.calls.append(kwargs)
            return json.dumps(
                [
                    {
                        "title": "知识复利",
                        "definition": "把研究产物沉淀为可复用知识。",
                        "summary": "持续把来源编译成概念、案例和链接。",
                        "related": ["LLM Wiki"],
                        "confidence": 0.8,
                        "tags": ["knowledge"],
                    }
                ],
                ensure_ascii=False,
            )

    source = SourceDocument(
        path=tmp_path / "source.md",
        title="Research",
        body="Body",
        source_type="research_report",
        domain_hint="personal_systems",
        tags=["research"],
        metadata={},
    )
    client = FakeChatClient()

    concepts = LLMConceptExtractor(model="test-model", client=client).extract(source)

    assert concepts[0].title == "知识复利"
    assert client.calls[0]["model"] == "test-model"
    assert "Research" in client.calls[0]["messages"][0]["content"]


def test_llm_concept_extractor_does_not_import_legacy_router():
    source = Path("src/personal_knowledge/compile/extractors.py").read_text(encoding="utf-8")

    assert "src.utils" not in source
    assert "utils.model_router" not in source
