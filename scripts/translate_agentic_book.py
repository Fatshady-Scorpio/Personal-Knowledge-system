#!/usr/bin/env python3
"""Extract chapters from Agentic Design Patterns PDF, translate to Chinese, and save as MD.

Usage:
    PYTHONPATH=. scripts/translate_agentic_book.py
"""

import json
import logging
import os
import re
import time
from pathlib import Path

import pdfplumber
import requests
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

PDF_PATH = Path(os.path.expanduser("~/Downloads/Agentic_Design_Patterns.pdf"))
OUTPUT_DIR = Path("/Users/samcao/Obsidian/wiki/raw/articles")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Chapter boundaries (page number = 1-indexed)
CHAPTERS = [
    (23, 35, "Chapter 1: Prompt Chaining", "第1章_提示链"),
    (36, 49, "Chapter 2: Routing", "第2章_路由"),
    (50, 64, "Chapter 3: Parallelization", "第3章_并行化"),
    (65, 78, "Chapter 4: Reflection", "第4章_反思"),
    (79, 99, "Chapter 5: Tool Use (Function Calling)", "第5章_工具使用"),
    (100, 112, "Chapter 6: Planning", "第6章_规划"),
    (113, 131, "Chapter 7: Multi-Agent Collaboration", "第7章_多智能体协作"),
    (132, 153, "Chapter 8: Memory Management", "第8章_记忆管理"),
    (154, 166, "Chapter 9: Learning and Adaptation", "第9章_学习与自适应"),
    (167, 182, "Chapter 10: Model Context Protocol", "第10章_模型上下文协议"),
    (183, 195, "Chapter 11: Goal Setting and Monitoring", "第11章_目标设定与监控"),
    (196, 203, "Chapter 12: Exception Handling and Recovery", "第12章_异常处理与恢复"),
    (204, 212, "Chapter 13: Human-in-the-Loop", "第13章_人在回路"),
    (213, 230, "Chapter 14: Knowledge Retrieval (RAG)", "第14章_知识检索"),
    (231, 245, "Chapter 15: Inter-Agent Communication", "第15章_智能体间通信"),
    (246, 261, "Chapter 16: Resource-Aware Optimization", "第16章_资源感知优化"),
    (262, 285, "Chapter 17: Reasoning Techniques", "第17章_推理技术"),
    (286, 305, "Chapter 18: Guardrails and Safety Patterns", "第18章_护栏与安全模式"),
    (306, 324, "Chapter 19: Evaluation and Monitoring", "第19章_评估与监控"),
    (325, 334, "Chapter 20: Prioritization", "第20章_优先级排序"),
    (335, 439, "Chapter 21: Exploration and Discovery", "第21章_探索与发现"),
]

API_KEY = os.getenv("BAILOU_API_KEY")
API_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1/messages"

TRANSLATE_MODEL = "qwen3.6-plus"
CHUNK_MAX_CHARS = 8000


def extract_chapter_text(pdf_path: Path, start_page: int, end_page: int) -> str:
    """Extract text from a chapter (pages are 1-indexed)."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i in range(start_page - 1, min(end_page, len(pdf.pages))):
            text = pdf.pages[i].extract_text()
            if text:
                pages_text.append(text)
    return "\n\n".join(pages_text)


def translate_chunk(text: str) -> str:
    """Translate a chunk of text to Chinese using LLM API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }

    prompt = (
        "You are a professional technical translator. Translate the following English text into fluent, "
        "natural Chinese (Simplified). Preserve all markdown formatting, code blocks, and technical terms. "
        "Keep code blocks and technical identifiers in English. Only output the translation, no extra commentary.\n\n"
        f"Text to translate:\n{text}"
    )

    payload = {
        "model": TRANSLATE_MODEL,
        "max_tokens": 16000,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}]
    }

    for attempt in range(3):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()
            # Find the text block (response may have thinking blocks first)
            for item in data["content"]:
                if item.get("type") == "text":
                    return item["text"]
            raise ValueError(f"No text block in response: {list(data.keys())}")
        except requests.exceptions.Timeout:
            logger.warning(f"Translation timeout (attempt {attempt+1}/3)")
            time.sleep(5 * (attempt + 1))
        except Exception as e:
            logger.error(f"Translation error (attempt {attempt+1}/3): {e}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Translation failed after 3 attempts")


def translate_full_text(text: str, chapter_name: str) -> str:
    """Translate a large text by splitting into chunks."""
    # Split by natural boundaries (double newlines, paragraphs)
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""
    for p in paragraphs:
        if len(current) + len(p) > CHUNK_MAX_CHARS and current:
            chunks.append(current)
            current = p
        else:
            current = current + "\n\n" + p if current else p
    if current:
        chunks.append(current)

    logger.info(f"  Split into {len(chunks)} chunks for translation")

    translated_parts = []
    for idx, chunk in enumerate(chunks):
        logger.info(f"  Translating chunk {idx+1}/{len(chunks)} ({len(chunk)} chars)")
        translated = translate_chunk(chunk)
        translated_parts.append(translated)
        # Rate limit
        time.sleep(2)

    return "\n\n".join(translated_parts)


def build_markdown(title: str, chinese_title: str, content: str, tags: list[str]) -> str:
    """Build markdown with frontmatter."""
    from datetime import datetime
    ts = datetime.now().isoformat()
    tags_str = ", ".join(tags)
    return f"""---
type: article
title: {title}
source: "Agentic Design Patterns - Antonio Gulli"
collected_at: {ts}
tags: [{tags_str}]
status: raw
---

# {chinese_title}

{content}
"""


def main():
    logger.info(f"Processing PDF: {PDF_PATH}")

    for start_page, end_page, chapter_name, chinese_name in CHAPTERS:
        logger.info(f"Extracting: {chapter_name} (pages {start_page}-{end_page})")

        # Check if already processed
        output_file = OUTPUT_DIR / f"20260412_{chinese_name}.md"
        if output_file.exists():
            logger.info(f"  Already exists, skipping: {output_file.name}")
            continue

        # Extract
        text = extract_chapter_text(PDF_PATH, start_page, end_page)
        if not text.strip():
            logger.warning(f"  No text extracted, skipping")
            continue

        logger.info(f"  Extracted {len(text)} chars")

        # Translate
        try:
            translated = translate_full_text(text, chapter_name)
        except RuntimeError as e:
            logger.error(f"  Translation failed: {e}, saving raw English version")
            translated = text

        # Build markdown
        tags = ["Agentic AI", "设计模式", "AI架构", chinese_name]
        md_content = build_markdown(chapter_name, chinese_name, translated, tags)

        # Save
        output_file.write_text(md_content, encoding="utf-8")
        logger.info(f"  Saved: {output_file.name}")
        time.sleep(1)

    logger.info("All chapters processed!")


if __name__ == "__main__":
    main()
