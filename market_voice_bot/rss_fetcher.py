"""Получение и разбор RSS-лент."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import feedparser

logger = logging.getLogger(__name__)


@dataclass
class NewsEntry:
    """Одна новость из RSS-ленты в удобном для нас виде."""

    title: str
    link: str
    summary: str
    published_parsed: tuple = field(default_factory=tuple)

    @classmethod
    def from_feed_entry(cls, entry) -> NewsEntry:
        return cls(
            title=getattr(entry, "title", "Без заголовка"),
            link=getattr(entry, "link", ""),
            summary=getattr(entry, "summary", ""),
            published_parsed=getattr(entry, "published_parsed", None) or (),
        )


def fetch_entries(url: str) -> list[NewsEntry]:
    """Читает одну RSS-ленту. Никогда не бросает исключение — логирует и возвращает []."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            logger.warning("Лента %s некорректна: %s", url, feed.get("bozo_exception"))
            return []
        entries = [NewsEntry.from_feed_entry(e) for e in feed.entries]
        # Отбрасываем записи без ссылки — по ссылке строится дедупликация.
        return [e for e in entries if e.link]
    except Exception:
        logger.exception("Не удалось прочитать ленту %s", url)
        return []


def fetch_all_entries(urls: list[str]) -> list[NewsEntry]:
    """Читает несколько лент подряд, ошибка в одной не мешает остальным."""
    all_entries: list[NewsEntry] = []
    for url in urls:
        all_entries.extend(fetch_entries(url))
    return all_entries


def sort_by_date_ascending(entries: list[NewsEntry]) -> list[NewsEntry]:
    """Сортирует от самых старых к самым новым — чтобы постить в хронологическом порядке."""
    return sorted(entries, key=lambda e: e.published_parsed or ())
