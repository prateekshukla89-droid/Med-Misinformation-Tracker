"""
SQLite database layer for storing collected and classified content.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)


class MisinfoDB:
    """SQLite storage for misinformation content."""

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        text TEXT,
        url TEXT,
        source_name TEXT,
        source_type TEXT,
        platform TEXT,
        published_date TEXT,
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP,
        search_query TEXT,
        raw_json TEXT
    );

    CREATE TABLE IF NOT EXISTS classifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_id INTEGER NOT NULL,
        theme TEXT,
        severity INTEGER,
        confidence REAL,
        summary TEXT,
        quote_fragment TEXT,
        time_period TEXT,
        classifier TEXT DEFAULT 'llm',
        classified_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (content_id) REFERENCES content(id)
    );

    CREATE TABLE IF NOT EXISTS trends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        date TEXT NOT NULL,
        interest_value INTEGER,
        geo TEXT DEFAULT 'US',
        collected_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_content_url ON content(url);
    CREATE INDEX IF NOT EXISTS idx_content_source ON content(source_type);
    CREATE INDEX IF NOT EXISTS idx_class_theme ON classifications(theme);
    CREATE INDEX IF NOT EXISTS idx_class_severity ON classifications(severity);
    CREATE INDEX IF NOT EXISTS idx_class_period ON classifications(time_period);
    CREATE INDEX IF NOT EXISTS idx_trends_keyword ON trends(keyword);
    """

    def __init__(self, db_path: str = "data/pharma_misinfo.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.executescript(self.SCHEMA)
        self.conn.commit()

    def insert_content(self, items: List[Dict]) -> List[int]:
        """Insert content items, skipping duplicates by URL."""
        ids = []
        cursor = self.conn.cursor()
        for item in items:
            # Skip if URL already exists
            if item.get("url"):
                existing = cursor.execute(
                    "SELECT id FROM content WHERE url = ?", (item["url"],)
                ).fetchone()
                if existing:
                    ids.append(existing["id"])
                    continue

            cursor.execute(
                """INSERT INTO content
                   (title, text, url, source_name, source_type, platform,
                    published_date, search_query, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    item.get("title", ""),
                    item.get("text", ""),
                    item.get("url", ""),
                    item.get("source_name", ""),
                    item.get("source_type", ""),
                    item.get("platform", ""),
                    item.get("published_date"),
                    item.get("search_query"),
                    json.dumps(item),
                ),
            )
            ids.append(cursor.lastrowid)

        self.conn.commit()
        logger.info(f"Inserted {len(ids)} content items")
        return ids

    def insert_classification(
        self,
        content_id: int,
        theme: str,
        severity: int,
        summary: str = "",
        quote_fragment: str = "",
        time_period: str = "",
        confidence: float = 1.0,
        classifier: str = "llm",
    ):
        """Insert a classification for a content item."""
        self.conn.execute(
            """INSERT INTO classifications
               (content_id, theme, severity, confidence, summary,
                quote_fragment, time_period, classifier)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (content_id, theme, severity, confidence, summary,
             quote_fragment, time_period, classifier),
        )
        self.conn.commit()

    def get_classified_content(
        self,
        theme: Optional[str] = None,
        min_severity: int = 1,
        time_period: Optional[str] = None,
    ) -> List[Dict]:
        """Query classified content with optional filters."""
        query = """
            SELECT c.*, cl.theme, cl.severity, cl.summary,
                   cl.quote_fragment, cl.time_period, cl.confidence
            FROM content c
            JOIN classifications cl ON c.id = cl.content_id
            WHERE cl.severity >= ?
        """
        params: List[Any] = [min_severity]

        if theme:
            query += " AND cl.theme = ?"
            params.append(theme)
        if time_period:
            query += " AND cl.time_period = ?"
            params.append(time_period)

        query += " ORDER BY cl.severity DESC, c.published_date"

        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_theme_counts(self) -> Dict[str, int]:
        """Get count of items per theme."""
        rows = self.conn.execute(
            "SELECT theme, COUNT(*) as cnt FROM classifications GROUP BY theme"
        ).fetchall()
        return {row["theme"]: row["cnt"] for row in rows}

    def get_timeline_data(self) -> Dict[str, Dict[str, int]]:
        """Get theme counts by time period for timeline visualization."""
        rows = self.conn.execute(
            """SELECT time_period, theme, COUNT(*) as cnt
               FROM classifications
               GROUP BY time_period, theme"""
        ).fetchall()

        result: Dict[str, Dict[str, int]] = {}
        for row in rows:
            period = row["time_period"]
            if period not in result:
                result[period] = {}
            result[period][row["theme"]] = row["cnt"]

        return result

    def export_csv(self, output_path: str):
        """Export all classified content to CSV."""
        import csv

        rows = self.get_classified_content()
        if not rows:
            logger.warning("No data to export")
            return

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"Exported {len(rows)} rows to {output_path}")

    def stats(self) -> Dict:
        """Return summary statistics."""
        content_count = self.conn.execute(
            "SELECT COUNT(*) as n FROM content"
        ).fetchone()["n"]
        classified_count = self.conn.execute(
            "SELECT COUNT(*) as n FROM classifications"
        ).fetchone()["n"]
        avg_severity = self.conn.execute(
            "SELECT AVG(severity) as avg FROM classifications"
        ).fetchone()["avg"]

        return {
            "total_content": content_count,
            "total_classified": classified_count,
            "avg_severity": round(avg_severity, 2) if avg_severity else 0,
            "themes": self.get_theme_counts(),
        }

    def close(self):
        self.conn.close()
