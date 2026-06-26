from pathlib import Path

from personal_knowledge.config import VaultConfig
from personal_knowledge.retrieve.v2_indexer import V2IndexManager


def test_v2_indexer_builds_domain_index_from_knowledge_dirs(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    concept_dir = config.domains_dir / "ai_agents" / "concepts"
    map_dir = config.domains_dir / "ai_agents" / "maps"
    concept_dir.mkdir(parents=True)
    map_dir.mkdir(parents=True)
    (concept_dir / "Transformer.md").write_text("# Transformer\n\n注意力机制", encoding="utf-8")
    (map_dir / "LLM.md").write_text("# LLM\n\n[[Transformer]]", encoding="utf-8")

    manager = V2IndexManager(config)
    results = manager.build_all()
    search_results = manager.get_index("ai_agents").search("注意力", top_k=5)

    assert results["ai_agents"] == 2
    assert search_results[0]["name"] == "Transformer"
    assert (config.indexes_dir / "ai_agents" / "index.json").exists()


def test_v2_indexer_ignores_empty_domains(tmp_path: Path):
    config = VaultConfig(vault_root=tmp_path / "wiki")
    (config.domains_dir / "content_creation" / "concepts").mkdir(parents=True)

    manager = V2IndexManager(config)

    assert manager.build_all() == {"content_creation": 0}
