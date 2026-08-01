from unittest.mock import MagicMock, patch

from market_voice_bot.ai_writer import AIGenerationError
from market_voice_bot.config import Settings
from market_voice_bot.main import run
from market_voice_bot.rss_fetcher import NewsEntry
from market_voice_bot.telegram_client import TelegramSendError


def _settings(**overrides):
    defaults = dict(
        groq_api_key="key",
        bot_token="token",
        channel_id="@chan",
        max_news_per_run=5,
    )
    defaults.update(overrides)
    return Settings(**defaults)


@patch("market_voice_bot.main.time.sleep", return_value=None)
@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_publishes_new_entry_and_marks_it_posted(
    mock_fetch, mock_storage_cls, mock_ai_cls, mock_tg_cls, mock_sleep
):
    news = NewsEntry("Title", "https://a.com/1", "summary", (2024, 1, 1, 0, 0, 0, 0, 0, 0))
    mock_fetch.return_value = [news]

    storage = MagicMock()
    storage.is_posted.return_value = False
    mock_storage_cls.return_value = storage

    ai_writer = MagicMock()
    ai_writer.generate_post.return_value = "Готовий пост"
    mock_ai_cls.return_value = ai_writer

    telegram = MagicMock()
    mock_tg_cls.return_value = telegram

    run(_settings())

    telegram.send_message.assert_called_once()
    storage.mark_posted.assert_called_once_with(news.link, news.title)


@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_skips_already_posted_entries(mock_fetch, mock_storage_cls, mock_ai_cls, mock_tg_cls):
    news = NewsEntry("Title", "https://a.com/1", "summary")
    mock_fetch.return_value = [news]

    storage = MagicMock()
    storage.is_posted.return_value = True
    mock_storage_cls.return_value = storage

    ai_writer = MagicMock()
    mock_ai_cls.return_value = ai_writer
    telegram = MagicMock()
    mock_tg_cls.return_value = telegram

    run(_settings())

    ai_writer.generate_post.assert_not_called()
    telegram.send_message.assert_not_called()


@patch("market_voice_bot.main.time.sleep", return_value=None)
@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_respects_max_news_per_run_limit(
    mock_fetch, mock_storage_cls, mock_ai_cls, mock_tg_cls, mock_sleep
):
    entries = [
        NewsEntry(f"Title {i}", f"https://a.com/{i}", "s", (2024, 1, i + 1, 0, 0, 0, 0, 0, 0))
        for i in range(5)
    ]
    mock_fetch.return_value = entries

    storage = MagicMock()
    storage.is_posted.return_value = False
    mock_storage_cls.return_value = storage

    ai_writer = MagicMock()
    ai_writer.generate_post.return_value = "Пост"
    mock_ai_cls.return_value = ai_writer

    telegram = MagicMock()
    mock_tg_cls.return_value = telegram

    run(_settings(max_news_per_run=2))

    assert telegram.send_message.call_count == 2


@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_does_not_mark_posted_when_ai_generation_fails(
    mock_fetch, mock_storage_cls, mock_ai_cls, mock_tg_cls
):
    news = NewsEntry("Title", "https://a.com/1", "summary")
    mock_fetch.return_value = [news]

    storage = MagicMock()
    storage.is_posted.return_value = False
    mock_storage_cls.return_value = storage

    ai_writer = MagicMock()
    ai_writer.generate_post.side_effect = AIGenerationError("boom")
    mock_ai_cls.return_value = ai_writer

    telegram = MagicMock()
    mock_tg_cls.return_value = telegram

    run(_settings())

    telegram.send_message.assert_not_called()
    storage.mark_posted.assert_not_called()


@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_does_not_mark_posted_when_telegram_send_fails(
    mock_fetch, mock_storage_cls, mock_ai_cls, mock_tg_cls
):
    news = NewsEntry("Title", "https://a.com/1", "summary")
    mock_fetch.return_value = [news]

    storage = MagicMock()
    storage.is_posted.return_value = False
    mock_storage_cls.return_value = storage

    ai_writer = MagicMock()
    ai_writer.generate_post.return_value = "Пост"
    mock_ai_cls.return_value = ai_writer

    telegram = MagicMock()
    telegram.send_message.side_effect = TelegramSendError("boom")
    mock_tg_cls.return_value = telegram

    run(_settings())

    storage.mark_posted.assert_not_called()


@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_marks_posted_when_ai_decides_to_skip(
    mock_fetch, mock_storage_cls, mock_ai_cls, mock_tg_cls
):
    news = NewsEntry("Title", "https://a.com/1", "summary")
    mock_fetch.return_value = [news]

    storage = MagicMock()
    storage.is_posted.return_value = False
    mock_storage_cls.return_value = storage

    ai_writer = MagicMock()
    ai_writer.generate_post.return_value = None  # ИИ решил пропустить
    mock_ai_cls.return_value = ai_writer

    telegram = MagicMock()
    mock_tg_cls.return_value = telegram

    run(_settings())

    telegram.send_message.assert_not_called()
    storage.mark_posted.assert_called_once_with(news.link, news.title)


@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_returns_early_when_no_entries_fetched(
    mock_fetch, mock_storage_cls, mock_ai_cls, mock_tg_cls
):
    mock_fetch.return_value = []
    mock_storage_cls.return_value = MagicMock()

    run(_settings())

    mock_ai_cls.return_value.generate_post.assert_not_called()
    mock_tg_cls.return_value.send_message.assert_not_called()
