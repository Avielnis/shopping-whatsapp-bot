import re
import sqlite3
from datetime import datetime

_WS_RE = re.compile(r"\s+")


def _normalize(name: str) -> str:
    return _WS_RE.sub(" ", name.strip())


class ShoppingListService:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'pending',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                collected_at TIMESTAMP
            )
            """
        )
        self._conn.commit()

    def add_items(self, names: list[str]):
        added, already_pending, restored = [], [], []
        for name in names:
            key = _normalize(name)
            row = self._conn.execute(
                "SELECT status FROM items WHERE normalized_name = ?", (key,)
            ).fetchone()
            if row is None:
                self._conn.execute(
                    "INSERT INTO items (name, normalized_name) VALUES (?, ?)",
                    (name.strip(), key),
                )
                added.append(name.strip())
            elif row[0] == "collected":
                self._conn.execute(
                    "UPDATE items SET status = 'pending', collected_at = NULL "
                    "WHERE normalized_name = ?",
                    (key,),
                )
                restored.append(name.strip())
            else:
                already_pending.append(name.strip())
        self._conn.commit()
        return added, already_pending, restored

    def remove_items(self, names: list[str]):
        removed, not_found = [], []
        for name in names:
            key = _normalize(name)
            cur = self._conn.execute("DELETE FROM items WHERE normalized_name = ?", (key,))
            (removed if cur.rowcount else not_found).append(name.strip())
        self._conn.commit()
        return removed, not_found

    def mark_collected(self, names: list[str]):
        marked, already_collected, not_found = [], [], []
        for name in names:
            key = _normalize(name)
            row = self._conn.execute(
                "SELECT status FROM items WHERE normalized_name = ?", (key,)
            ).fetchone()
            if row is None:
                not_found.append(name.strip())
            elif row[0] == "collected":
                already_collected.append(name.strip())
            else:
                self._conn.execute(
                    "UPDATE items SET status = 'collected', collected_at = ? "
                    "WHERE normalized_name = ?",
                    (datetime.now().isoformat(), key),
                )
                marked.append(name.strip())
        self._conn.commit()
        return marked, already_collected, not_found

    def unmark(self, names: list[str]):
        unmarked, not_found = [], []
        for name in names:
            key = _normalize(name)
            cur = self._conn.execute(
                "UPDATE items SET status = 'pending', collected_at = NULL "
                "WHERE normalized_name = ? AND status = 'collected'",
                (key,),
            )
            (unmarked if cur.rowcount else not_found).append(name.strip())
        self._conn.commit()
        return unmarked, not_found

    def resolve(self, tokens: list[str]) -> list[str]:
        """Translate 1-based position numbers (matching the numbered
        `רשימה` output) into item names; non-numeric tokens pass through
        unchanged."""
        numbered = None
        resolved = []
        for token in tokens:
            if token.isdigit():
                if numbered is None:
                    pending, collected = self.get_list()
                    numbered = pending + collected
                index = int(token) - 1
                resolved.append(numbered[index] if 0 <= index < len(numbered) else token)
            else:
                resolved.append(token)
        return resolved

    def get_list(self):
        pending = [
            row[0]
            for row in self._conn.execute(
                "SELECT name FROM items WHERE status = 'pending' ORDER BY added_at"
            )
        ]
        collected = [
            row[0]
            for row in self._conn.execute(
                "SELECT name FROM items WHERE status = 'collected' ORDER BY collected_at"
            )
        ]
        return pending, collected

    def clear_all(self):
        self._conn.execute("DELETE FROM items")
        self._conn.commit()
