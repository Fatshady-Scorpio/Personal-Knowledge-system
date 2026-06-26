from personal_knowledge.migration.path_mapper import map_legacy_path


def test_maps_raw_article_to_sources():
    assert map_legacy_path("raw/articles/A.md") == "10_sources/articles/A.md"


def test_maps_ai_concept_to_v2_domain():
    assert (
        map_legacy_path("domains/ai/concepts/Transformer.md")
        == "20_knowledge/domains/ai_agents/concepts/Transformer.md"
    )


def test_maps_product_topic_to_map():
    assert (
        map_legacy_path("domains/product/topics/Growth.md")
        == "20_knowledge/domains/product_growth/maps/Growth.md"
    )


def test_maps_clipping_to_sources():
    assert map_legacy_path("Clippings/Page.md") == "10_sources/clippings/Page.md"
