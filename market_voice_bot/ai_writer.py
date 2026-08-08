"""Генерация текста поста из сырой новости с помощью DeepSeek (LLM)."""

from __future__ import annotations

import logging
import time

from openai import OpenAI

from .rss_fetcher import NewsEntry

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ти — досвідчений фінансовий аналітик та автор Telegram-каналу Market Voice. Твоя мета — перетворювати сирі новини на стислі, інсайдерські та живі пости для криптоінвесторів.

ПРАВИЛА ФОРМАТУВАННЯ ТА СТИЛЮ (СУВОРО):
1. Жодних шаблонів та ярликів ("Заголовок:", "Суть:", "Аналіз:", "Висновок:"). Пиши одразу фінальний текст посту.
2. Структура посту та правила форматування (використовуй ТІЛЬКИ HTML-теги):
   - Заголовок: Одне релевантне емодзі + звичайний текст (без тегів). Приклад: 📊 Крипторинок сьогодні: головні події
   - Основна частина (1-2 короткі абзаци).
     * Обов'язково виділяй <b>жирним</b> ключові цифри, відсотки, суми та найважливіші показники (наприклад: <b>майже подвоїлася</b>, <b>у 4-5 разів</b>).
     * Виділяй ключові терміни чи сутності <u>підкресленим</u> (за допомогою тегу <u>термін</u>), якщо хочеш привернути до них увагу.
   - 📌 Market Voice: (Твій авторський інсайт одним рядком). Сам текст інсайту бери в <i>курсив</i> (тег <i>текст</i>).
   - Хештеги: В самому кінці тексту обов'язково додай 3-4 актуальні тематичні хештеги через пробіл (наприклад: #BTC #DeFi #макро).
3. Мова: виключно грамотна українська. Жодних русизмів.
4. Якщо вхідна новина не несе цінності (вода, чутки без фактів, реклама, немає конкретики) — у відповідь видай лише одне слово: SKIP.
5. Заборонено використовувати Markdown-розмітку (**, *, _). Тільки HTML: <b>, <i>, <u>."""

SKIP_MARKER = "SKIP"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


class AIGenerationError(Exception):
    """Генерация не удалась после всех попыток (проблема с API/сетью)."""


class AIWriter:
    """Обёртка над DeepSeek-клиентом для генерации постов из новостей."""

    def __init__(self, api_key: str, model: str) -> None:
        # Используем OpenAI клиент, так как DeepSeek API совместим с ним
        self._client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        self._model = model

    def generate_post(self, news: NewsEntry) -> str | None:
        """Генерирует текст поста.

        Возвращает None, если ИИ счёл новость не стоящей публикации (SKIP).
        Бросает AIGenerationError, если после нескольких попыток так и не
        удалось получить ответ от модели.
        """
        raw_text = f"Заголовок: {news.title}\nТекст: {news.summary}"

        last_error: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                completion = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": raw_text},
                    ],
                    temperature=0.4,
                )
                text = (completion.choices[0].message.content or "").strip()

                if text.upper() == SKIP_MARKER:
                    logger.info("ИИ пропустил новость: %s", news.title)
                    return None

                return text
            except Exception as exc:  # ошибки сети/квоты DeepSeek
                last_error = exc
                logger.warning(
                    "Ошибка генерации поста (попытка %s/%s): %s",
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)

        raise AIGenerationError(
            f"Не удалось сгенерировать пост для «{news.title}» после {MAX_RETRIES} попыток"
        ) from last_error
