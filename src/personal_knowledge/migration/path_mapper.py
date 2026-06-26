from __future__ import annotations

from pathlib import PurePosixPath


DOMAIN_MAP = {
    "ai": "ai_agents",
    "product": "product_growth",
    "investment": "business_investment",
    "general": "personal_systems",
}


def map_legacy_path(relative_path: str) -> str:
    path = PurePosixPath(relative_path)
    parts = path.parts

    if len(parts) >= 3 and parts[0] == "raw":
        source_type = {
            "articles": "articles",
            "papers": "papers",
            "videos": "videos",
            "notes": "work_notes",
            "qa": "conversations",
        }.get(parts[1], "work_notes")
        return PurePosixPath("10_sources", source_type, *parts[2:]).as_posix()

    if len(parts) >= 4 and parts[0] == "domains":
        domain = DOMAIN_MAP.get(parts[1], "personal_systems")
        object_dir = "maps" if parts[2] == "topics" else parts[2]
        return PurePosixPath("20_knowledge", "domains", domain, object_dir, *parts[3:]).as_posix()

    if len(parts) >= 2 and parts[0] == "Clippings":
        return PurePosixPath("10_sources", "clippings", *parts[1:]).as_posix()

    if len(parts) >= 2 and parts[0] == "reports":
        return PurePosixPath("40_outputs", "research_reports", *parts[1:]).as_posix()

    if len(parts) >= 3 and parts[0] == "wiki":
        object_dir = "maps" if parts[1] == "topics" else parts[1]
        return PurePosixPath("20_knowledge", "domains", "personal_systems", object_dir, *parts[2:]).as_posix()

    return PurePosixPath("90_archive", "legacy", *parts).as_posix()
