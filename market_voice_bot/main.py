"""Точка входа: собрать новости → сгенерировать посты → опубликовать в Telegram."""

from __future__ import annotations

import logging
import time

from .ai_writer import AIGenerationError, AIWriter
from .config import ConfigError, Settings, setup_logging
from .rss_fetcher import fetch_all_entries, sort_by_date_ascending
from .storage import Storage
from .telegram_client import TelegramClient, TelegramSendError

logger = logging.getLogger(__name__)

PAUSE_BETWEEN_POSTS_SECONDS = 3
DB_PRUNE_KEEP_LAST = 1000


def run(settings: Settings) -> None:
    storage = Storage(settings.db_path)
    ai_writer = AIWriter(settings.groq_api_key, settings.groq_model)
    telegram = TelegramClient(settings.bot_token, settings.channel_id)

    logger.info("Проверяю %s RSS-источник(ов)...", len(settings.rss_urls))
    all_entries = fetch_all_entries(settings.rss_urls)
    if not all_entries:
        logger.error("Не удалось получить новости ни из одного источника.")
        return

    # Новой считается любая ссылка, которой ещё нет в хранилище — это надёжнее,
    # чем сравнивать с одной "последней" ссылкой, и не ломается при изменении
    # порядка записей в ленте.
    fresh_entries = [e for e in all_entries if not storage.is_posted(e.link)]
    fresh_entries = sort_by_date_ascending(fresh_entries)

    if not fresh_entries:
        logger.info("Новых новостей нет. Всё актуально.")
        return

    if len(fresh_entries) > settings.max_news_per_run:
        logger.info(
            "Найдено %s новых новостей, обработаю последние %s (лимит за запуск).",
            len(fresh_entries),
            settings.max_news_per_run,
        )
        fresh_entries = fresh_entries[-settings.max_news_per_run :]
    else:
        logger.info("Найдено новых новостей для обработки: %s", len(fresh_entries))

    for news in fresh_entries:
        logger.info("Обрабатываю: %s", news.title)

        try:
            post_text = ai_writer.generate_post(news)
        except AIGenerationError as exc:
            logger.error("%s — новость НЕ отмечена, попробую снова в следующий раз.", exc)
            continue

        if post_text is None:
            # ИИ сам решил, что новость не стоит публикации — запоминаем, чтобы
            # не пытаться сгенерировать пост из неё повторно.
            storage.mark_posted(news.link, news.title)
            continue

        full_post = f"{post_text}\n\nДжерело: {news.link}"

        try:
            telegram.send_message(full_post)
        except TelegramSendError as exc:
            logger.error(
                "%s — пост для «%s» НЕ отмечен, попробую снова в следующий раз.",
                exc,
                news.title,
            )
            continue

        logger.info("Опубликовано: %s", news.title)
        storage.mark_posted(news.link, news.title)
        time.sleep(PAUSE_BETWEEN_POSTS_SECONDS)

    storage.prune(keep_last=DB_PRUNE_KEEP_LAST)


def main() -> None:
    try:
        settings = Settings.from_env()
    except ConfigError as exc:
        setup_logging("INFO")
        logging.getLogger(__name__).error(str(exc))
        raise SystemExit(1) from exc

    setup_logging(settings.log_level)
    logger.info("Market Voice Bot запущен.")
    run(settings)
    logger.info("Готово.")


if __name__ == "__main__":
    main()
