from __future__ import annotations

import json
import pickle
import re
from pathlib import Path
from typing import Optional

import jieba
from rank_bm25 import BM25Okapi

from personal_knowledge.config import VaultConfig


KNOWLEDGE_SUBDIRS = ["concepts", "maps", "principles", "cases", "playbooks", "questions"]
_JIEBA_READY = False


def tokenize(text: str) -> list[str]:
    global _JIEBA_READY
    if not _JIEBA_READY:
        jieba.setLogLevel(20)
        _JIEBA_READY = True

    tokens: list[str] = []
    for link in re.findall(r"\[\[([^\]]+)\]\]", text):
        tokens.append(link.replace(" ", "_"))

    cleaned = re.sub(r"\[\[[^\]]+\]\]", " ", text)
    tokens.extend(token.lower() for token in re.findall(r"[a-zA-Z]{4,}", cleaned))
    tokens.extend(token.strip() for token in jieba.lcut(cleaned) if token.strip())

    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        result.append(token)
    return result


class V2DomainIndex:
    def __init__(self, config: VaultConfig, domain: str):
        self.config = config
        self.domain = domain
        self.domain_dir = config.domains_dir / domain
        self.index_dir = config.indexes_dir / domain
        self.bm25: Optional[BM25Okapi] = None
        self.doc_ids: list[str] = []
        self.doc_tokens: list[list[str]] = []
        self.doc_contents: dict[str, str] = {}
        self.doc_paths: dict[str, str] = {}

    def build(self) -> int:
        self.doc_ids.clear()
        self.doc_tokens.clear()
        self.doc_contents.clear()
        self.doc_paths.clear()

        for subdir in KNOWLEDGE_SUBDIRS:
            directory = self.domain_dir / subdir
            if not directory.exists():
                continue
            for md_file in sorted(directory.glob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                tokens = tokenize(content)
                if not tokens:
                    continue
                doc_id = md_file.stem
                if doc_id in self.doc_contents:
                    doc_id = f"{subdir}/{md_file.stem}"
                self.doc_ids.append(doc_id)
                self.doc_tokens.append(tokens)
                self.doc_contents[doc_id] = content
                self.doc_paths[doc_id] = str(md_file)

        self.bm25 = BM25Okapi(self.doc_tokens) if self.doc_tokens else None
        return len(self.doc_ids)

    def save(self) -> Path:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        with (self.index_dir / "bm25.pkl").open("wb") as handle:
            pickle.dump(self.bm25, handle)
        with (self.index_dir / "index.json").open("w", encoding="utf-8") as handle:
            json.dump(
                {
                    "domain": self.domain,
                    "doc_ids": self.doc_ids,
                    "doc_tokens": self.doc_tokens,
                    "doc_paths": self.doc_paths,
                },
                handle,
                ensure_ascii=False,
            )
        with (self.index_dir / "contents.json").open("w", encoding="utf-8") as handle:
            json.dump(self.doc_contents, handle, ensure_ascii=False)
        return self.index_dir

    def load(self) -> bool:
        index_path = self.index_dir / "index.json"
        if not index_path.exists():
            return False
        data = json.loads(index_path.read_text(encoding="utf-8"))
        self.doc_ids = data["doc_ids"]
        self.doc_tokens = data["doc_tokens"]
        self.doc_paths = data.get("doc_paths", {})
        with (self.index_dir / "bm25.pkl").open("rb") as handle:
            self.bm25 = pickle.load(handle)
        self.doc_contents = json.loads((self.index_dir / "contents.json").read_text(encoding="utf-8"))
        return True

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        if self.bm25 is None:
            return []
        query_tokens = tokenize(query)
        if not query_tokens:
            return []
        scores = self.bm25.get_scores(query_tokens)
        results = []
        query_token_set = set(query_tokens)
        for index, score in enumerate(scores):
            overlap = len(query_token_set.intersection(self.doc_tokens[index]))
            if score <= 0 and overlap == 0:
                continue
            doc_id = self.doc_ids[index]
            results.append(
                {
                    "name": doc_id,
                    "score": float(score) if score > 0 else float(overlap) * 0.001,
                    "content": self.doc_contents.get(doc_id, ""),
                    "path": self.doc_paths.get(doc_id, ""),
                    "source": "bm25",
                }
            )
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]


class V2IndexManager:
    def __init__(self, config: VaultConfig):
        self.config = config
        self._indexes: dict[str, V2DomainIndex] = {}

    def get_index(self, domain: str) -> V2DomainIndex:
        normalized = self.config.normalize_domain(domain)
        if normalized not in self._indexes:
            index = V2DomainIndex(self.config, normalized)
            if not index.load():
                index.build()
                index.save()
            self._indexes[normalized] = index
        return self._indexes[normalized]

    def build_all(self) -> dict[str, int]:
        if not self.config.domains_dir.exists():
            return {}
        results: dict[str, int] = {}
        for domain_dir in sorted(self.config.domains_dir.iterdir()):
            if not domain_dir.is_dir():
                continue
            index = V2DomainIndex(self.config, domain_dir.name)
            count = index.build()
            index.save()
            self._indexes[domain_dir.name] = index
            results[domain_dir.name] = count
        return results

    def build_domain(self, domain: str) -> int:
        normalized = self.config.normalize_domain(domain)
        index = V2DomainIndex(self.config, normalized)
        count = index.build()
        index.save()
        self._indexes[normalized] = index
        return count
