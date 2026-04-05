"""Tests for the summarizer module."""

import pytest
from pathlib import Path

from src.processor.summarizer import Summarizer


class TestSummarizer:
    """Test cases for Summarizer class."""

    @pytest.fixture
    def sample_text(self) -> str:
        """Sample text for testing."""
        return """
        人工智能（AI）是计算机科学的一个分支，旨在创造能够执行需要人类智能的任务的系统。
        这些任务包括学习、推理、问题解决、感知和理解语言。AI 的应用包括机器学习、
        自然语言处理、计算机视觉和机器人技术。近年来，随着深度学习和大数据的发展，
        AI 取得了显著进步，在医疗诊断、自动驾驶、语音助手等领域都有广泛应用。
        """

    @pytest.fixture
    def summarizer(self) -> Summarizer:
        """Create a Summarizer instance."""
        return Summarizer()

    def test_process_returns_dict(self, summarizer: Summarizer, sample_text: str):
        """Test that process returned a dictionary with expected keys."""
        result = summarizer.process(sample_text)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "category" in result
        assert "tags" in result
        assert "processed_at" in result
        assert isinstance(result["tags"], list)

    def test_process_to_markdown_contains_sections(self, summarizer: Summarizer, sample_text: str):
        """Test that markdown output contains expected sections."""
        markdown = summarizer.process_to_markdown(sample_text, title="测试文章")

        assert "# 测试文章" in markdown
        assert "## 摘要" in markdown
        assert "## 标签" in markdown
        assert "## 原始内容" in markdown

    def test_save_to_file_creates_file(self, summarizer: Summarizer, sample_text: str, tmp_path: Path):
        """Test that save_to_file creates a markdown file."""
        filepath = summarizer.save_to_file(
            sample_text,
            title="测试文章",
            output_dir=tmp_path
        )

        assert filepath.exists()
        assert filepath.suffix == ".md"
        assert "测试文章" in filepath.name
