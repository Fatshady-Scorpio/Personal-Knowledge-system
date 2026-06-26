from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from personal_knowledge.compile.v2_concept_writer import ConceptDraft
from personal_knowledge.compile.v2_source_compiler import SourceDocument
from personal_knowledge.llm import ChatClient, chat_client_from_env


def _extract_json_text(text: str) -> str:
    stripped = text.strip()
    if "```json" in stripped:
        return stripped.split("```json", 1)[1].split("```", 1)[0].strip()
    if "```" in stripped:
        return stripped.split("```", 1)[1].split("```", 1)[0].strip()
    return stripped


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def parse_concept_drafts(text: str) -> list[ConceptDraft]:
    data = json.loads(_extract_json_text(text))
    if not isinstance(data, list):
        raise ValueError("concept extraction response must be a JSON list")
    concepts: list[ConceptDraft] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        concepts.append(
            ConceptDraft(
                title=title,
                definition=str(item.get("definition") or ""),
                summary=str(item.get("summary") or ""),
                related=_as_string_list(item.get("related")),
                confidence=float(item.get("confidence") or 0.5),
                tags=_as_string_list(item.get("tags")),
            )
        )
    return concepts


class JsonFileConceptExtractor:
    def __init__(self, path: Path):
        self.path = path

    def extract(self, source: SourceDocument) -> list[ConceptDraft]:
        return parse_concept_drafts(self.path.read_text(encoding="utf-8"))


class LLMConceptExtractor:
    def __init__(self, model: str = "qwen3.6-plus", client: ChatClient | None = None):
        self.model = model
        self.client = client

    def extract(self, source: SourceDocument) -> list[ConceptDraft]:
        prompt = self._build_prompt(source)
        client = self.client or chat_client_from_env()
        response = client.call(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.2,
            timeout=120,
        )
        return parse_concept_drafts(response)

    def _build_prompt(self, source: SourceDocument) -> str:
        tags = ", ".join(source.tags) if source.tags else "none"
        return f"""You are maintaining Sam's personal LLM Wiki.

Extract durable knowledge objects from this source. Return only a JSON array.

Source title: {source.title}
Source type: {source.source_type}
Domain hint: {source.domain_hint}
Tags: {tags}

Source body:
{source.body[:9000]}

Return JSON array items with:
- title
- definition
- summary
- related
- confidence
- tags

Focus on reusable concepts, principles, cases, playbooks, or open questions. Avoid generic summaries.
"""
