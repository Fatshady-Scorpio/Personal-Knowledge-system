"""Raw material processor for Agentic Wiki.

Handles reading and validating raw materials from the raw/ directory.
"""

import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RawMaterial:
    """Represents a raw material item."""

    def __init__(
        self,
        path: Path,
        title: str,
        content: str,
        raw_type: str,
        source: Optional[str] = None,
        collected_at: Optional[datetime] = None,
        tags: Optional[list[str]] = None,
        status: str = "raw",
        user_notes: Optional[str] = None,
    ):
        self.path = path
        self.title = title
        self.content = content
        self.raw_type = raw_type  # article, video, paper, note
        self.source = source
        self.collected_at = collected_at or datetime.now()
        self.tags = tags or []
        self.status = status  # raw, compiled, reviewed
        self.user_notes = user_notes

    def __repr__(self):
        return f"RawMaterial(title='{self.title}', type='{self.raw_type}', status='{self.status}')"


class RawProcessor:
    """Process raw materials from the raw/ directory."""

    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def read(self, path: Path) -> RawMaterial:
        """Read a raw material file.

        Args:
            path: Path to the raw markdown file

        Returns:
            RawMaterial object with parsed content

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if not path.exists():
            raise FileNotFoundError(f"Raw material not found: {path}")

        content = path.read_text(encoding="utf-8")
        metadata, body = self._parse_frontmatter(content)

        # Validate required fields
        if "type" not in metadata:
            raise ValueError(f"Missing 'type' in frontmatter: {path}")

        # Extract user notes (section after "---" if present)
        user_notes = None
        if "\n---\n" in body:
            parts = body.split("\n---\n", 1)
            body = parts[0].strip()
            user_notes = parts[1].strip() if len(parts) > 1 else None

        return RawMaterial(
            path=path,
            title=metadata.get("title", path.stem),
            content=body,
            raw_type=metadata.get("type", "article"),
            source=metadata.get("source"),
            collected_at=self._parse_date(metadata.get("collected_at")),
            tags=metadata.get("tags", []),
            status=metadata.get("status", "raw"),
            user_notes=user_notes,
        )

    def list_all(self, status: Optional[str] = None) -> list[Path]:
        """List all raw materials.

        Args:
            status: Filter by status (raw, compiled, reviewed)

        Returns:
            List of paths to raw material files
        """
        all_files = []
        for subdir in ["articles", "videos", "papers", "notes"]:
            subpath = self.raw_dir / subdir
            if subpath.exists():
                all_files.extend(subpath.glob("*.md"))

        if status:
            # Filter by status
            filtered = []
            for path in all_files:
                try:
                    material = self.read(path)
                    if material.status == status:
                        filtered.append(path)
                except Exception as e:
                    logger.warning(f"Failed to read {path}: {e}")
            return filtered

        return all_files

    def create(
        self,
        title: str,
        content: str,
        raw_type: str,
        source: Optional[str] = None,
        tags: Optional[list[str]] = None,
        user_notes: Optional[str] = None,
    ) -> Path:
        """Create a new raw material file.

        Args:
            title: Title of the material
            content: Main content
            raw_type: Type (article, video, paper, note)
            source: Original source URL
            tags: List of tags
            user_notes: Optional user notes

        Returns:
            Path to the created file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d")
        safe_title = self._slugify(title)[:50]
        filename = f"{timestamp}_{safe_title}.md"

        # Determine subdirectory
        subdir_map = {
            "article": "articles",
            "video": "videos",
            "paper": "papers",
            "note": "notes",
        }
        subdir = subdir_map.get(raw_type, "articles")
        output_path = self.raw_dir / subdir / filename

        # Build frontmatter
        frontmatter = f"""---
type: {raw_type}
title: {title}
source: {source or ''}
collected_at: {datetime.now().isoformat()}
tags: {tags or []}
status: raw
---

# {title}

{content}
"""

        if user_notes:
            frontmatter += f"""
---

## 我的思考

{user_notes}
"""

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(frontmatter, encoding="utf-8")
        logger.info(f"Created raw material: {output_path}")

        return output_path

    def update_status(self, path: Path, status: str) -> None:
        """Update the status of a raw material.

        Args:
            path: Path to the raw material
            status: New status (raw, compiled, reviewed)
        """
        material = self.read(path)
        material.status = status

        # Rewrite file with updated status
        content = path.read_text(encoding="utf-8")
        metadata, body = self._parse_frontmatter(content)
        metadata["status"] = status

        new_content = self._build_frontmatter(metadata) + body
        path.write_text(new_content, encoding="utf-8")

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        """Parse YAML frontmatter from markdown content.

        Returns:
            Tuple of (metadata dict, body content)
        """
        if not content.startswith("---"):
            return {}, content

        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content

        # Parse YAML frontmatter (simple parser, no external dependency)
        metadata = {}
        for line in parts[1].strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Parse lists
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip() for v in value[1:-1].split(",")]

                metadata[key] = value

        return metadata, parts[2].strip()

    def _build_frontmatter(self, metadata: dict) -> str:
        """Build YAML frontmatter from metadata dict."""
        lines = ["---"]
        for key, value in metadata.items():
            if isinstance(value, list):
                lines.append(f"{key}: {value}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---\n")
        return "\n".join(lines)

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            return None

    def _slugify(self, text: str) -> str:
        """Convert text to a safe filename slug."""
        # Simple slugify - replace spaces and remove special chars
        slug = text.replace(" ", "_").replace("/", "_")
        slug = "".join(c for c in slug if c.isalnum() or c in "_-")
        return slug
