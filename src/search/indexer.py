"""Search Indexer — BM25 inverted index per domain.

Builds and persists BM25 indexes for each wiki domain using jieba for
Chinese tokenization. Indexes are stored under wiki/domains/{domain}/.index/.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Optional

import jieba
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

# Jieba: load user dictionary if available (improves domain term segmentation)
_JIEBA_INIT_DONE = False


def _ensure_jieba():
    global _JIEBA_INIT_DONE
    if _JIEBA_INIT_DONE:
        return
    jieba.setLogLevel(logging.ERROR)
    _JIEBA_INIT_DONE = True


def tokenize(text: str) -> list[str]:
    """Tokenize text for indexing.

    - Chinese: jieba cut
    - English: lowercase + alphanumeric tokens (4+ chars)
    - Wiki links [[name]]: extracted as-is
    """
    _ensure_jieba()
    import re

    tokens = []

    # Extract wiki links as single tokens
    wiki_links = re.findall(r"\[\[([^\]]+)\]\]", text)
    for link in wiki_links:
        tokens.append(link.replace(" ", "_"))

    # Remove wiki link syntax before general tokenization
    cleaned = re.sub(r"\[\[[^\]]+\]\]", " ", text)

    # English words (4+ chars for meaningful terms)
    english = re.findall(r"[a-zA-Z]{4,}", cleaned)
    tokens.extend(t.lower() for t in english)

    # Chinese + mixed: jieba segmentation
    chinese_tokens = jieba.lcut(cleaned)
    tokens.extend(
        t.strip()
        for t in chinese_tokens
        if len(t.strip()) >= 1 and not t.isspace()
    )

    # Deduplicate while preserving order
    seen = set()
    result = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


class DomainIndex:
    """BM25 index for a single wiki domain."""

    def __init__(self, domain: str, wiki_root: Path):
        self.domain = domain
        self.domain_dir = wiki_root / "domains" / domain
        self.index_dir = self.domain_dir / ".index"
        self.concepts_dir = self.domain_dir / "concepts"
        self.topics_dir = self.domain_dir / "topics"

        # BM25 state
        self.bm25: Optional[BM25Okapi] = None
        self.doc_ids: list[str] = []  # entry_name → index position
        self.doc_tokens: list[list[str]] = []  # tokenized docs
        self.doc_contents: dict[str, str] = {}  # entry_name → full content

    def build(self) -> int:
        """Scan all entries, tokenize, and build BM25 index.

        Returns:
            Number of indexed entries
        """
        self.doc_ids.clear()
        self.doc_tokens.clear()
        self.doc_contents.clear()

        for directory in [self.concepts_dir, self.topics_dir]:
            if not directory.exists():
                continue
            for md_file in sorted(directory.glob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                name = md_file.stem
                tokens = tokenize(content)
                if not tokens:
                    continue

                self.doc_ids.append(name)
                self.doc_tokens.append(tokens)
                self.doc_contents[name] = content

        if self.doc_tokens:
            self.bm25 = BM25Okapi(self.doc_tokens)
        else:
            self.bm25 = None

        logger.info(
            f"Built BM25 index for domain '{self.domain}': "
            f"{len(self.doc_ids)} entries"
        )
        return len(self.doc_ids)

    def save(self) -> Path:
        """Persist index to disk.

        Returns:
            Path to saved index directory
        """
        self.index_dir.mkdir(parents=True, exist_ok=True)

        with open(self.index_dir / "bm25.pkl", "wb") as f:
            pickle.dump(self.bm25, f)

        index_data = {
            "domain": self.domain,
            "doc_ids": self.doc_ids,
            "doc_tokens": self.doc_tokens,
        }
        with open(self.index_dir / "index.json", "w", encoding="utf-8") as f:
            # store tokens as simple lists (JSON-serializable)
            json.dump(index_data, f, ensure_ascii=False)

        # Store doc contents separately (can be large)
        with open(self.index_dir / "contents.json", "w", encoding="utf-8") as f:
            json.dump(self.doc_contents, f, ensure_ascii=False)

        logger.info(f"Saved index to {self.index_dir}")
        return self.index_dir

    def load(self) -> bool:
        """Load persisted index from disk.

        Returns:
            True if index was loaded, False if not found
        """
        if not (self.index_dir / "index.json").exists():
            return False

        with open(self.index_dir / "index.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        self.doc_ids = data["doc_ids"]
        self.doc_tokens = data["doc_tokens"]

        with open(self.index_dir / "bm25.pkl", "rb") as f:
            self.bm25 = pickle.load(f)

        with open(self.index_dir / "contents.json", "r", encoding="utf-8") as f:
            self.doc_contents = json.load(f)

        logger.info(
            f"Loaded index for domain '{self.domain}': "
            f"{len(self.doc_ids)} entries"
        )
        return True

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Search indexed entries for a query.

        Args:
            query: User query string
            top_k: Maximum results to return

        Returns:
            List of dicts with name, score, content
        """
        if self.bm25 is None:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Build results sorted by score descending
        results = []
        for i, score in enumerate(scores):
            if score <= 0:
                continue
            results.append({
                "name": self.doc_ids[i],
                "score": float(scores[i]),
                "content": self.doc_contents.get(self.doc_ids[i], ""),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_entry(self, name: str) -> Optional[str]:
        """Get full content of a specific entry by name."""
        return self.doc_contents.get(name)

    def get_entry_names(self) -> list[str]:
        """Return all indexed entry names."""
        return list(self.doc_ids)


class IndexManager:
    """Manage BM25 indexes across all domains."""

    def __init__(self, wiki_root: Path):
        self.wiki_root = wiki_root
        self.domains_dir = wiki_root / "domains"
        self._indexes: dict[str, DomainIndex] = {}

    def get_index(self, domain: str) -> DomainIndex:
        """Get or create a DomainIndex for the given domain."""
        if domain not in self._indexes:
            idx = DomainIndex(domain, self.wiki_root)
            # Try loading persisted index first
            if not idx.load():
                idx.build()
                idx.save()
            self._indexes[domain] = idx
        return self._indexes[domain]

    def build_all(self) -> dict[str, int]:
        """Build indexes for all domains.

        Returns:
            Dict of {domain: entry_count}
        """
        if not self.domains_dir.exists():
            return {}

        results = {}
        for domain_dir in sorted(self.domains_dir.iterdir()):
            if not domain_dir.is_dir():
                continue
            domain = domain_dir.name
            idx = DomainIndex(domain, self.wiki_root)
            count = idx.build()
            idx.save()
            self._indexes[domain] = idx
            results[domain] = count
            logger.info(f"Domain '{domain}': {count} entries indexed")

        return results
