"""Загрузка и валидация конфигурации бота из переменных окружения."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

# Обновили дефолтную модель для DeepSeek
DEFAULT_RSS_URLS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cryptoslate.com/feed/",
]

DEFAULT_MODEL = "deepseek-chat" 
DEFAULT_DB_PATH = "data/state.db"
DEFAULT_MAX_NEWS_PER_RUN = 5


class ConfigError(RuntimeError):
    """Выбрасывается, если обязательная конфигурация отсутствует или некорректна."""


@dataclass(frozen=True)
class Settings:
    """Полная конфигурация запуска бота."""

    deepseek_api_key: str
    bot_token: str
    channel_id: str
    deepseek_model: str = DEFAULT_MODEL
    rss_urls: list[str] = field(default_factory=lambda: list(DEFAULT_RSS_URLS))
    db_path: str = DEFAULT_DB_PATH
    max_news_per_run: int = DEFAULT_MAX_NEWS_PER_RUN
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> Settings:
        """Собирает настройки из переменных окружения и валидирует обязательные поля."""
        deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY")
        bot_token = os.environ.get("BOT_TOKEN")
        channel_id = os.environ.get("CHANNEL_ID")

        missing = [
            name
            for name, value in (
                ("DEEPSEEK_API_KEY", deepseek_api_key),
                ("BOT_TOKEN", bot_token),
                ("CHANNEL_ID", channel_id),
            )
            if not value
        ]
        if missing:
            raise ConfigError(
                "Отсутствуют обязательные переменные окружения: " + ", ".join(missing)
            )

        rss_urls_env = os.environ.get("RSS_URLS")
        rss_urls = (
            [u.strip() for u in rss_urls_env.split(",") if u.strip()]
            if rss_urls_env
            else list(DEFAULT_RSS_URLS)
        )

        max_news_env = os.environ.get("MAX_NEWS_PER_RUN")
        try:
            max_news_per_run = int(max_news_env) if max_news_env else DEFAULT_MAX_NEWS_PER_RUN
        except ValueError as exc:
            raise ConfigError("MAX_NEWS_PER_RUN должен быть целым числом") from exc

        return cls(
            deepseek_api_key=deepseek_api_key,  # type: ignore[arg-type]
            bot_token=bot_token,  # type: ignore[arg-type]
            channel_id=channel_id,  # type: ignore[arg-type]
            deepseek_model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
            rss_urls=rss_urls,
            db_path=os.environ.get("DB_PATH", DEFAULT_DB_PATH),
            max_news_per_run=max_news_per_run,
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
        )


def setup_logging(level: str = "INFO") -> None:
    """Настраивает единый формат логов для всего приложения."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
