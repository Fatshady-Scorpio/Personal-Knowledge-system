"""Priority filter for content selection."""

from typing import Optional
from datetime import datetime, timedelta


class PriorityFilter:
    """Filter content by priority to avoid information overload."""

    # High priority sources
    HIGH_PRIORITY_SOURCES = {
        "机器之心 RSS",
        "量子位 RSS",
        "arXiv cs.AI",
        "arXiv cs.LG",
        "Sebastian Raschka",
        "Jay Alammar",
    }

    # User interest keywords
    INTEREST_KEYWORDS = {
        "LLM",
        "Transformer",
        "RAG",
        "微调",
        "Fine-tuning",
        "推理优化",
        "Inference",
        "Agent",
        "多模态",
        "Multimodal",
        "强化学习",
        "Reinforcement Learning",
        "大模型",
        "语言模型",
    }

    # Ignore keywords
    IGNORE_KEYWORDS = {
        "广告",
        "推广",
        "赞助",
        "招聘",
        "课程推荐",
    }

    def __init__(self, user_interests: Optional[dict] = None):
        """Initialize priority filter.

        Args:
            user_interests: Optional override from config/user_interests.yaml
        """
        if user_interests:
            if "keywords" in user_interests:
                self.INTEREST_KEYWORDS = set(user_interests["keywords"])
            if "ignore_keywords" in user_interests:
                self.IGNORE_KEYWORDS = set(user_interests["ignore_keywords"])
            if "high_priority_sources" in user_interests:
                self.HIGH_PRIORITY_SOURCES = set(user_interests["high_priority_sources"])

    def calculate_score(self, item: dict) -> int:
        """Calculate priority score for an item.

        Args:
            item: Item dictionary with title, source, published, etc.

        Returns:
            Priority score (higher = more important)
        """
        score = 0
        title = item.get("title", "").lower()
        source = item.get("name", item.get("source", ""))

        # Source priority (0-3 points)
        if source in self.HIGH_PRIORITY_SOURCES:
            score += 3
        elif any(hp in source for hp in self.HIGH_PRIORITY_SOURCES):
            score += 2

        # Title keyword matching (0-5 points)
        for keyword in self.INTEREST_KEYWORDS:
            if keyword.lower() in title:
                score += 1

        # Recency bonus (0-2 points)
        published = item.get("published")
        if published:
            try:
                pub_date = self._parse_date(published)
                if pub_date and pub_date > datetime.now() - timedelta(hours=24):
                    score += 2
                elif pub_date and pub_date > datetime.now() - timedelta(days=3):
                    score += 1
            except:
                pass

        return score

    def should_process(self, item: dict, min_score: int = 3) -> bool:
        """Determine if an item should be processed.

        Args:
            item: Item dictionary
            min_score: Minimum score threshold

        Returns:
            True if item should be processed
        """
        # Check ignore keywords first
        title = item.get("title", "").lower()
        content = item.get("content", "").lower()

        for keyword in self.IGNORE_KEYWORDS:
            if keyword.lower() in title or keyword.lower() in content:
                return False

        # Calculate score
        score = self.calculate_score(item)
        return score >= min_score

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime.

        Args:
            date_str: Date string in various formats

        Returns:
            datetime object or None
        """
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",  # RFC 822
            "%Y-%m-%dT%H:%M:%S%z",       # ISO 8601
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None
