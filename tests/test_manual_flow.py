"""Test the manual collection + auto-summary flow."""

import pytest
from pathlib import Path

from src.processor.summarizer import Summarizer
from src.utils.config import get_config


class TestManualFlow:
    """Test the Phase 1 manual collection flow."""

    @pytest.fixture
    def sample_article(self) -> str:
        """Load sample article."""
        project_root = Path(__file__).parent.parent
        article_path = project_root / "data" / "sample_article.txt"
        with open(article_path, "r", encoding="utf-8") as f:
            return f.read()

    def test_process_sample_article(self, sample_article: str, tmp_path: Path):
        """Test processing the sample article."""
        summarizer = Summarizer(output_dir=tmp_path)

        result = summarizer.process(
            sample_article,
            source_url="https://example.com/article"
        )

        assert "摘要" in result["summary"] or "对比" in result["summary"]
        assert result["category"] in ["AI", "技术"]
        assert len(result["tags"]) > 0

    def test_save_markdown_file(self, sample_article: str, tmp_path: Path):
        """Test saving processed article as markdown."""
        summarizer = Summarizer(output_dir=tmp_path)

        filepath = summarizer.save_to_file(
            sample_article,
            title="GPT-4 vs Claude 对比分析",
            source_url="https://example.com/article"
        )

        assert filepath.exists()

        content = filepath.read_text(encoding="utf-8")
        assert "---" in content  # Frontmatter
        assert "category:" in content
        assert "tags:" in content
        assert "## 摘要" in content
