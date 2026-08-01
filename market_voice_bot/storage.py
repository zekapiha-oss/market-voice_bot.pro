"""Хранилище состояния бота (какие новости уже обработаны).

Раньше состояние хранилось в одной строке текстового файла (ссылка на
последнюю опубликованную новость), что легко ломалось при переупорядочивании
RSS-ленты или при параллельном/повторном запуске. Здесь вместо этого
используется SQLite: каждая обработанная ссылка запоминается отдельно,
поэтому дубликаты исключены, а порядок в ленте больше не важен.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class Storage:
    """Простой SQLite-репозиторий обработанных ссылок на новости."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posted_links (
                    link TEXT PRIMARY KEY,
                    title TEXT,
                    posted_at TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def is_posted(self, link: str) -> bool:
        """Проверяет, обрабатывалась ли уже эта ссылка (опубликована или скипнута)."""
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM posted_links WHERE link = ?", (link,)).fetchone()
            return row is not None

    def mark_posted(self, link: str, title: str = "") -> None:
        """Отмечает ссылку как обработанную."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO posted_links (link, title, posted_at) VALUES (?, ?, ?)",
                (link, title, datetime.now(timezone.utc).isoformat()),
            )

    def prune(self, keep_last: int = 1000) -> None:
        """Оставляет только последние `keep_last` записей, чтобы БД не росла бесконечно."""
        with self._connect() as conn:
            conn.execute(
                """
                DELETE FROM posted_links
                WHERE link NOT IN (
                    SELECT link FROM posted_links
                    ORDER BY posted_at DESC
                    LIMIT ?
                )
                """,
                (keep_last,),
            )

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM posted_links").fetchone()
            return row[0] if row else 0
