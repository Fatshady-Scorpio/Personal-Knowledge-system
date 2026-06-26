from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


DEFAULT_DOMAIN_MAP = {
    "ai": "ai_agents",
    "product": "product_growth",
    "investment": "business_investment",
    "general": "personal_systems",
}


@dataclass(frozen=True)
class VaultConfig:
    vault_root: Path
    staging_vault: Path | None = None
    project_root: Path | None = None
    domain_map: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_DOMAIN_MAP))

    @property
    def inbox_dir(self) -> Path:
        return self.vault_root / "00_inbox"

    @property
    def sources_dir(self) -> Path:
        return self.vault_root / "10_sources"

    @property
    def research_reports_dir(self) -> Path:
        return self.sources_dir / "research_reports"

    @property
    def knowledge_dir(self) -> Path:
        return self.vault_root / "20_knowledge"

    @property
    def domains_dir(self) -> Path:
        return self.knowledge_dir / "domains"

    @property
    def outputs_dir(self) -> Path:
        return self.vault_root / "40_outputs"

    @property
    def system_dir(self) -> Path:
        return self.vault_root / "_system"

    @property
    def indexes_dir(self) -> Path:
        return self.system_dir / "indexes"

    @property
    def manifests_dir(self) -> Path:
        return self.system_dir / "manifests"

    @property
    def knowledge_manifest_path(self) -> Path:
        return self.manifests_dir / "knowledge_manifest.jsonl"

    @property
    def operation_log_path(self) -> Path:
        return self.system_dir / "reports" / "operations.jsonl"

    def normalize_domain(self, domain: str | None) -> str:
        if not domain:
            return "personal_systems"
        return self.domain_map.get(domain, domain)


def _as_path(value: Any) -> Path | None:
    if value is None:
        return None
    text = str(value).strip()
    return Path(text).expanduser() if text else None


def load_vault_config(path: Path | None = None) -> VaultConfig:
    config_path = path or Path("config/vault.yaml")
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    vault_root = _as_path(data.get("current_vault"))
    if vault_root is None:
        raise ValueError(f"current_vault is required in {config_path}")
    staging_vault = _as_path(data.get("staging_vault"))
    project_root = _as_path(data.get("project_root"))
    domain_map = data.get("domains") or {}
    if not isinstance(domain_map, dict):
        raise ValueError(f"domains must be a mapping in {config_path}")
    merged_map = dict(DEFAULT_DOMAIN_MAP)
    merged_map.update({str(key): str(value) for key, value in domain_map.items()})
    return VaultConfig(
        vault_root=vault_root,
        staging_vault=staging_vault,
        project_root=project_root,
        domain_map=merged_map,
    )
