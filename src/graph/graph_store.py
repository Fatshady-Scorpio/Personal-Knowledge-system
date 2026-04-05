"""Knowledge graph storage using SQLite and NetworkX."""

import sqlite3
import networkx as nx
from pathlib import Path
from typing import Optional


class GraphStore:
    """Store and query knowledge graph."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.graph = nx.DiGraph()

    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Nodes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content_preview TEXT,
                category TEXT,
                tags TEXT,
                created_at TEXT
            )
        """)

        # Edges table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                source_id TEXT,
                target_id TEXT,
                relation_type TEXT,
                weight REAL DEFAULT 1.0,
                PRIMARY KEY (source_id, target_id, relation_type)
            )
        """)

        conn.commit()
        conn.close()

    def add_node(self, node_id: str, title: str, content_preview: str = "",
                 category: str = "", tags: list[str] = None):
        """Add a node to the graph."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO nodes (id, title, content_preview, category, tags, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (node_id, title, content_preview[:200], category,
              ",".join(tags) if tags else ""))

        conn.commit()
        conn.close()

        # Also add to NetworkX graph
        self.graph.add_node(node_id, title=title, category=category)

    def add_edge(self, source_id: str, target_id: str, relation_type: str = "related"):
        """Add an edge between two nodes."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO edges (source_id, target_id, relation_type, weight)
            VALUES (?, ?, ?, 1.0)
        """, (source_id, target_id, relation_type))

        conn.commit()
        conn.close()

        # Also add to NetworkX graph
        self.graph.add_edge(source_id, target_id, relation_type=relation_type)

    def get_related(self, node_id: str, limit: int = 10) -> list[dict]:
        """Get nodes related to the given node."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT n.id, n.title, n.category, e.relation_type
            FROM edges e
            JOIN nodes n ON e.target_id = n.id
            WHERE e.source_id = ?
            LIMIT ?
        """, (node_id, limit))

        results = [
            {"id": row[0], "title": row[1], "category": row[2], "relation": row[3]}
            for row in cursor.fetchall()
        ]

        conn.close()
        return results
