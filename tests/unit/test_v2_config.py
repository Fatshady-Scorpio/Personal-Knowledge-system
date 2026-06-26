from pathlib import Path

from personal_knowledge.config.vault import VaultConfig, load_vault_config
from personal_knowledge.ingest.source_writer import SOURCE_TYPE_DIRS


def test_load_vault_config_from_yaml(tmp_path: Path):
    config_path = tmp_path / "vault.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"current_vault: {tmp_path / 'wiki'}",
                f"staging_vault: {tmp_path / 'staging'}",
                f"project_root: {tmp_path / 'project'}",
                "domains:",
                "  ai: ai_agents",
                "  product: product_growth",
            ]
        ),
        encoding="utf-8",
    )

    config = load_vault_config(config_path)

    assert config.vault_root == tmp_path / "wiki"
    assert config.sources_dir == tmp_path / "wiki" / "10_sources"
    assert config.knowledge_dir == tmp_path / "wiki" / "20_knowledge"
    assert config.indexes_dir == tmp_path / "wiki" / "_system" / "indexes"
    assert config.domain_map["ai"] == "ai_agents"


def test_vault_config_can_be_constructed_directly(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")

    assert config.research_reports_dir == tmp_path / "wiki" / "10_sources" / "research_reports"
    assert config.operation_log_path == tmp_path / "wiki" / "_system" / "reports" / "operations.jsonl"


def test_vault_config_uses_canonical_obsidian_vault():
    config = load_vault_config(Path("config/vault.yaml"))

    assert str(config.vault_root) == "/Users/samcao/Obsidian/wiki"
    assert config.domain_map["ai"] == "ai_agents"
    assert config.domain_map["general"] == "personal_systems"
    assert "research_report" in SOURCE_TYPE_DIRS
    assert "work_note" in SOURCE_TYPE_DIRS
