"""Клиент Telegram Bot API с обработкой rate-limit и повторными попытками."""

from __future__ import annotations

import logging
import time

import requests

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4096
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 15


class TelegramSendError(Exception):
    """Сообщение не удалось доставить после всех попыток."""


class TelegramClient:
    """Тонкая обёртка над методом sendMessage Telegram Bot API."""

    def __init__(self, bot_token: str, channel_id: str) -> None:
        self._url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self._channel_id = channel_id

    def send_message(self, text: str, parse_mode: str = "HTML") -> None:
        """Отправляет сообщение. Ретраит при 429/5xx, обрезает слишком длинный текст."""
        if len(text) > TELEGRAM_MESSAGE_LIMIT:
            logger.warning(
                "Текст поста (%s симв.) превышает лимит Telegram (%s), обрезаю.",
                len(text),
                TELEGRAM_MESSAGE_LIMIT,
            )
            text = text[: TELEGRAM_MESSAGE_LIMIT - 1] + "…"

        payload = {"chat_id": self._channel_id, "text": text, "parse_mode": parse_mode}

        for attempt in range(1, MAX_RETRIES + 1):
            response = requests.post(self._url, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)

            if response.status_code == 200:
                return

            if response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                logger.warning("Telegram флуд-контроль, жду %s сек...", retry_after)
                time.sleep(retry_after)
                continue

            logger.error("Ошибка Telegram API (%s): %s", response.status_code, response.text)
            if attempt < MAX_RETRIES:
                time.sleep(3 * attempt)

        raise TelegramSendError(f"Не удалось отправить сообщение после {MAX_RETRIES} попыток")
