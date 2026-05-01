"""Knowledge Weaver — Q&A evaluation & promotion to wiki.

The core of "结网" (knowledge weaving):
1. Evaluates saved Q&A for knowledge value
2. Extracts new concepts from high-quality answers
3. Promotes Q&A to wiki entries or merges into existing ones
4. Updates domain indexes incrementally

Pipeline:
    Q&A file ──> Evaluation ──> [High: New concept / Medium: Merge / Low: Keep as QA]
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from ..compiler.link_extractor import LinkExtractor
from ..compiler.wiki_builder import WikiBuilder
from ..domain_manager import DomainManager
from ..utils.model_router import get_router

logger = logging.getLogger(__name__)


class KnowledgeValue(Enum):
    """Classification of Q&A knowledge value."""
    HIGH = "high"      # New concept or relationship → create wiki entry
    MEDIUM = "medium"  # Supplement existing → merge into entry
    LOW = "low"        # One-time question → keep as QA only


@dataclass
class WeaverResult:
    """Result of weaving a Q&A into the wiki."""
    value: KnowledgeValue
    action: str  # Description of what was done
    target_path: Optional[Path] = None
    merged_into: Optional[str] = None  # Entry name if merged


class KnowledgeWeaver:
    """Evaluate and weave Q&A into the wiki knowledge network."""

    def __init__(
        self,
        wiki_root: Path,
        qa_dir: Path,
        model: str = "qwen3.6-plus",
    ):
        self.wiki_root = wiki_root
        self.qa_dir = qa_dir
        self.model = model
        self.router = get_router()
        self.domain_manager = DomainManager()

    def evaluate_qa(self, question: str, answer: str) -> KnowledgeValue:
        """Evaluate a Q&A's knowledge value.

        Uses LLM to judge whether the Q&A contains:
        - New concepts worth creating wiki entries
        - Supplemental info worth merging
        - Only situational advice (keep as QA)

        Args:
            question: The question
            answer: The generated answer

        Returns:
            KnowledgeValue classification
        """
        prompt = f"""请评估以下问答的知识价值：

**问题**: {question}

**回答**: {answer[:1500]}

请判断这个问答属于哪类知识价值（仅返回一个词）：
- **high**: 包含新概念或新关系，值得创建新的 wiki 词条
- **medium**: 补充了已有词条的信息，值得合并到现有词条
- **low**: 一次性问答，仅作为 QA 记录保留

仅返回一个词（high/medium/low），不要其他内容。"""

        try:
            response = self.router.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1,
            ).strip().lower()

            if "high" in response:
                return KnowledgeValue.HIGH
            elif "medium" in response:
                return KnowledgeValue.MEDIUM
            else:
                return KnowledgeValue.LOW

        except Exception as e:
            logger.warning(f"Failed to evaluate Q&A: {e}")
            return KnowledgeValue.LOW

    def extract_concepts(self, question: str, answer: str) -> list[dict]:
        """Extract new concepts from a high-value Q&A.

        Args:
            question: The question
            answer: The generated answer

        Returns:
            List of concept dictionaries (title, definition, summary, related)
        """
        prompt = f"""请从以下问答中提取值得创建为 wiki 词条的核心概念：

**问题**: {question}

**回答**: {answer}

请提取 1-3 个核心概念，以 JSON 格式返回：

```json
[
    {{
        "title": "概念名称",
        "definition": "一句话定义（50 字以内）",
        "summary": "详细解释（200-300 字）",
        "related": ["相关概念 1", "相关概念 2"],
        "key_points": ["关键点 1", "关键点 2"]
    }}
]
```

仅返回 JSON 数组，不要其他内容。"""

        try:
            import json

            response = self.router.call(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3,
            )

            response = response.strip()
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()

            concepts = json.loads(response)
            logger.info(f"Extracted {len(concepts)} concepts from Q&A")
            return concepts

        except Exception as e:
            logger.error(f"Failed to extract concepts: {e}")
            return []

    def find_similar_entry(self, concept_title: str, domain: str) -> Optional[str]:
        """Find an existing wiki entry similar to a new concept.

        Uses BM25 to check if a similar entry already exists.

        Args:
            concept_title: New concept title
            domain: Target domain

        Returns:
            Similar entry name if found, None otherwise
        """
        from .indexer import DomainIndex, tokenize

        index = DomainIndex(domain, self.wiki_root)
        if not index.load():
            index.build()

        results = index.search(concept_title, top_k=3)
        if results and results[0]["score"] > 5.0:
            return results[0]["name"]
        return None

    def weave_qa(self, qa_path: Path, domain: Optional[str] = None) -> WeaverResult:
        """Weave a single Q&A file into the wiki.

        Pipeline:
        1. Read Q&A file
        2. Evaluate knowledge value
        3. Route to appropriate action (create/merge/keep)

        Args:
            qa_path: Path to Q&A markdown file
            domain: Override domain (auto-detected if None)

        Returns:
            WeaverResult describing the action taken
        """
        content = qa_path.read_text(encoding="utf-8")
        question, answer = self._parse_qa(content)

        if not question or not answer:
            return WeaverResult(
                value=KnowledgeValue.LOW,
                action="解析 Q&A 文件失败",
            )

        # Evaluate
        value = self.evaluate_qa(question, answer)

        if value == KnowledgeValue.HIGH:
            return self._create_entries(question, answer, domain)
        elif value == KnowledgeValue.MEDIUM:
            return self._merge_entry(question, answer, domain)
        else:
            return WeaverResult(
                value=value,
                action="保留为 QA 记录",
                target_path=qa_path,
            )

    def weave_all_pending(self, domain: Optional[str] = None) -> list[WeaverResult]:
        """Weave all unprocessed Q&A files.

        Args:
            domain: Target domain (auto-detected per Q&A if None)

        Returns:
            List of WeaverResult for each Q&A
        """
        if not self.qa_dir.exists():
            return []

        results = []
        for qa_file in sorted(self.qa_dir.glob("*.md")):
            if qa_file.is_file():
                result = self.weave_qa(qa_file, domain)
                results.append(result)
                logger.info(f"Weaved {qa_file.name}: {result.value.value} → {result.action}")

        return results

    def _create_entries(
        self,
        question: str,
        answer: str,
        domain: Optional[str] = None,
    ) -> WeaverResult:
        """Create new wiki entries from a high-value Q&A."""
        # Determine domain
        if not domain:
            domain = self.domain_manager.classify_text(question + " " + answer)

        # Extract concepts
        concepts = self.extract_concepts(question, answer)
        if not concepts:
            return WeaverResult(
                value=KnowledgeValue.HIGH,
                action="提取概念失败，保留为 QA",
            )

        # Create wiki entries using WikiBuilder infrastructure
        from ..compiler.raw_processor import RawProcessor, RawMaterial
        from ..compiler.wiki_builder import WikiBuilder

        raw_dir = self.wiki_root.parent / "raw"
        qa_subdir = raw_dir / "qa"
        qa_subdir.mkdir(parents=True, exist_ok=True)

        raw_processor = RawProcessor(raw_dir)

        # Create a RawMaterial from the Q&A (path must be under raw_dir)
        material = RawMaterial(
            path=qa_subdir / f"{self._slugify(question)[:60]}.md",
            title=f"QA_{self._slugify(question)[:50]}",
            content=answer,
            raw_type="qa",
            source="Q&A 沉淀",
            tags=[],
            status="raw",
            user_notes=f"问题: {question}",
        )

        builder = WikiBuilder(raw_processor, self.wiki_root, domain=domain)

        created_paths = []
        for concept in concepts:
            path = builder._create_wiki_entry(concept, material)
            if path:
                created_paths.append(path)

        if created_paths:
            # Incremental index update (no LLM call)
            from ..compiler.index_generator import IndexGenerator
            gen = IndexGenerator(self.wiki_root, domain=domain)
            new_concepts = [
                {"title": c.get("title", ""), "tags": []}
                for c in concepts
            ]
            gen.update_incremental(new_concepts)

            return WeaverResult(
                value=KnowledgeValue.HIGH,
                action=f"创建 {len(created_paths)} 个新词条",
                target_path=created_paths[0],
            )

        return WeaverResult(
            value=KnowledgeValue.HIGH,
            action="创建词条失败",
        )

    def _merge_entry(
        self,
        question: str,
        answer: str,
        domain: Optional[str] = None,
    ) -> WeaverResult:
        """Merge Q&A content into an existing wiki entry."""
        if not domain:
            domain = self.domain_manager.classify_text(question + " " + answer)

        # Try to find the most relevant entry
        from .indexer import DomainIndex

        index = DomainIndex(domain, self.wiki_root)
        if not index.load():
            return WeaverResult(
                value=KnowledgeValue.MEDIUM,
                action="索引未找到，保留为 QA",
            )

        results = index.search(question, top_k=1)
        if not results:
            return WeaverResult(
                value=KnowledgeValue.MEDIUM,
                action="未找到相关词条，保留为 QA",
            )

        target_name = results[0]["name"]
        target_content = index.get_entry(target_name)
        if not target_content:
            return WeaverResult(
                value=KnowledgeValue.MEDIUM,
                action=f"词条 {target_name} 内容未找到",
            )

        # Append Q&A content as supplementary section
        supplement = f"""
---

## 补充（来自 Q&A）

**问题**: {question}

{answer[:500]}
"""
        # Find the entry file
        entry_path = None
        for md_file in (index.concepts_dir / "*.md").parent.glob("*.md"):
            if md_file.stem == target_name:
                entry_path = md_file
                break
        if not entry_path:
            for md_file in index.topics_dir.glob("*.md"):
                if md_file.stem == target_name:
                    entry_path = md_file
                    break

        if entry_path:
            entry_path.write_text(
                target_content + supplement,
                encoding="utf-8",
            )
            logger.info(f"Merged Q&A into {entry_path}")

            return WeaverResult(
                value=KnowledgeValue.MEDIUM,
                action=f"合并到词条 [[{target_name}]]",
                target_path=entry_path,
                merged_into=target_name,
            )

        return WeaverResult(
            value=KnowledgeValue.MEDIUM,
            action="未找到词条文件，保留为 QA",
        )

    def _parse_qa(self, content: str) -> tuple[Optional[str], Optional[str]]:
        """Extract question and answer from a Q&A markdown file."""
        # Try YAML frontmatter first
        if content.startswith("---"):
            parts = content.split("---", 3)
            if len(parts) >= 3:
                body = parts[2].strip()
                metadata = {}
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        metadata[key.strip()] = value.strip()

                question = metadata.get("question", "")
                if "# 问题" in body:
                    # Extract from body structure
                    body_parts = body.split("# 回答", 1)
                    if len(body_parts) >= 2:
                        question = body_parts[0].replace("# 问题", "").strip()
                        answer = body_parts[1].strip()
                    else:
                        answer = body
                    return question or None, answer or None

                # If question is in frontmatter, extract answer from body
                if question:
                    # Find first markdown heading after frontmatter
                    body_start = body.find("\n# ")
                    if body_start >= 0:
                        answer = body[body_start:].strip()
                    else:
                        answer = body
                    return question, answer or None

        # Fallback: try to find "# 问题" and "# 回答" headers
        if "# 问题" in content and "# 回答" in content:
            parts = content.split("# 回答", 1)
            question = parts[0].replace("# 问题", "").strip()
            answer = parts[1].strip()
            return question or None, answer or None

        return None, None

    def _slugify(self, text: str) -> str:
        """Convert text to a safe filename slug."""
        slug = text.replace(" ", "_").replace("/", "_")
        slug = "".join(c for c in slug if c.isalnum() or c in "_-")
        return slug
