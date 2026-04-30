"""Domain Manager — dynamic domain classification and management.

Reads config/domains.yaml, classifies wiki entries into domains,
supports add/merge/remove/list operations.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent.parent


@dataclass
class Domain:
    """A knowledge domain."""
    id: str
    name: str
    keywords: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    enabled: bool = True

    @property
    def dir_path(self) -> Path:
        return ROOT_DIR / "wiki" / "domains" / self.id

    @property
    def concepts_dir(self) -> Path:
        return self.dir_path / "concepts"

    @property
    def topics_dir(self) -> Path:
        return self.dir_path / "topics"


class DomainManager:
    """Manage knowledge domains: classification, CRUD, merge."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or ROOT_DIR / "config" / "domains.yaml"
        self.domains: dict[str, Domain] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load domain configuration from YAML."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Domain config not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        for domain_id, config in data.get("domains", {}).items():
            self.domains[domain_id] = Domain(
                id=domain_id,
                name=config.get("name", domain_id),
                keywords=config.get("keywords", []),
                tags=config.get("tags", []),
                enabled=config.get("enabled", True),
            )

    def save_config(self) -> None:
        """Save current domain configuration to YAML."""
        data = {"domains": {}}
        for domain_id, domain in self.domains.items():
            data["domains"][domain_id] = {
                "name": domain.name,
                "keywords": domain.keywords,
                "tags": domain.tags,
                "enabled": domain.enabled,
            }
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def list_domains(self) -> list[Domain]:
        """Return all enabled domains."""
        return [d for d in self.domains.values() if d.enabled]

    def get_domain(self, domain_id: str) -> Optional[Domain]:
        """Get a domain by ID."""
        return self.domains.get(domain_id)

    def ensure_dirs(self, domain_id: str) -> None:
        """Ensure domain directories exist."""
        domain = self.domains.get(domain_id)
        if not domain:
            raise ValueError(f"Domain not found: {domain_id}")
        domain.concepts_dir.mkdir(parents=True, exist_ok=True)
        domain.topics_dir.mkdir(parents=True, exist_ok=True)

    # ── Classification ──────────────────────────────────────────

    def classify_entry(self, filepath: Path) -> str:
        """Classify a wiki entry file into a domain.

        Uses frontmatter tags first, then keyword matching on content.
        Falls back to 'general' if no match.
        """
        content = filepath.read_text(encoding="utf-8")
        frontmatter = self._parse_frontmatter(content)
        tags = frontmatter.get("tags", [])
        title = frontmatter.get("title", filepath.stem)

        # Strategy 1: tag matching (highest priority)
        for domain_id, domain in self.domains.items():
            if not domain.enabled or domain_id == "general":
                continue
            if any(t in domain.tags for t in tags):
                return domain_id

        # Strategy 2: keyword matching on title + content
        text = (title + " " + content[:3000]).lower()
        best_score = 0
        best_domain = "general"

        for domain_id, domain in self.domains.items():
            if not domain.enabled or domain_id == "general":
                continue
            score = sum(1 for kw in domain.keywords if kw.lower() in text)
            if score > best_score:
                best_score = score
                best_domain = domain_id

        return best_domain

    def classify_text(self, text: str) -> str:
        """Classify arbitrary text into a domain.

        Used by agent_query to determine query domain.
        """
        text = text.lower()
        best_score = 0
        best_domain = "general"

        for domain_id, domain in self.domains.items():
            if not domain.enabled or domain_id == "general":
                continue
            score = sum(1 for kw in domain.keywords if kw.lower() in text)
            if score > best_score:
                best_score = score
                best_domain = domain_id

        return best_domain

    def get_entry_domain(self, filepath: Path) -> str:
        """Determine which domain a file currently belongs to.

        Returns empty string if not in any domain directory.
        """
        try:
            rel = filepath.relative_to(ROOT_DIR / "wiki" / "domains")
            return rel.parts[0]
        except ValueError:
            return ""

    # ── CRUD Operations ─────────────────────────────────────────

    def add_domain(self, domain_id: str, name: str, keywords: list[str], tags: list[str]) -> Domain:
        """Add a new domain."""
        if domain_id in self.domains:
            raise ValueError(f"Domain already exists: {domain_id}")
        domain = Domain(id=domain_id, name=name, keywords=keywords, tags=tags)
        self.domains[domain_id] = domain
        self.ensure_dirs(domain_id)
        self.save_config()
        return domain

    def remove_domain(self, domain_id: str, move_to: str = "general") -> None:
        """Remove a domain, moving its entries to another domain."""
        if domain_id not in self.domains:
            raise ValueError(f"Domain not found: {domain_id}")
        if domain_id == "general":
            raise ValueError("Cannot remove the general domain")

        # Move entries
        old_domain = self.domains[domain_id]
        if old_domain.dir_path.exists():
            target_domain = self.domains.get(move_to)
            if target_domain:
                self.ensure_dirs(move_to)
                self._move_entries(old_domain.dir_path, target_domain.dir_path)

        # Remove from config
        del self.domains[domain_id]
        self.save_config()

    def merge_domains(self, from_id: str, to_id: str) -> None:
        """Merge one domain into another."""
        if from_id not in self.domains or to_id not in self.domains:
            raise ValueError(f"Domain not found: {from_id} or {to_id}")

        from_domain = self.domains[from_id]
        to_domain = self.domains[to_id]

        self.ensure_dirs(to_id)

        # Merge keywords and tags
        for kw in from_domain.keywords:
            if kw not in to_domain.keywords:
                to_domain.keywords.append(kw)
        for tag in from_domain.tags:
            if tag not in to_domain.tags:
                to_domain.tags.append(tag)

        # Move entries
        if from_domain.dir_path.exists():
            self._move_entries(from_domain.dir_path, to_domain.dir_path)

        # Remove source domain
        del self.domains[from_id]
        self.save_config()

    def status(self) -> dict:
        """Get status of all domains."""
        result = {}
        for domain_id, domain in self.domains.items():
            concepts = list(domain.concepts_dir.glob("*.md")) if domain.concepts_dir.exists() else []
            topics = list(domain.topics_dir.glob("*.md")) if domain.topics_dir.exists() else []
            result[domain_id] = {
                "name": domain.name,
                "enabled": domain.enabled,
                "concepts": len(concepts),
                "topics": len(topics),
                "keywords": len(domain.keywords),
                "tags": len(domain.tags),
            }
        return result

    # ── Internal helpers ────────────────────────────────────────

    def _parse_frontmatter(self, content: str) -> dict:
        """Parse YAML frontmatter from markdown content."""
        metadata = {}
        if not content.startswith("---"):
            return metadata
        parts = content.split("---", 3)
        if len(parts) < 3:
            return metadata
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                value = value.strip()
                # Parse list values like [a, b, c]
                if value.startswith("[") and value.endswith("]"):
                    try:
                        value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",")]
                    except Exception:
                        value = []
                metadata[key.strip()] = value
        return metadata

    def _move_entries(self, src_dir: Path, dst_dir: Path) -> None:
        """Move all markdown files from src_dir tree to dst_dir tree."""
        for md_file in src_dir.rglob("*.md"):
            if md_file.is_file():
                dest = dst_dir / md_file.relative_to(src_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                md_file.rename(dest)

        # Remove empty directories
        for dir_path in sorted(src_dir.rglob("*"), reverse=True):
            if dir_path.is_dir():
                try:
                    dir_path.rmdir()
                except OSError:
                    pass
