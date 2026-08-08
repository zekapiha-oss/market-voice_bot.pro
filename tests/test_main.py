import pytest
from unittest.mock import patch, MagicMock
from market_voice_bot.main import run
from market_voice_bot.config import Settings
from market_voice_bot.rss_fetcher import NewsEntry

@pytest.fixture
def mock_settings(tmp_path):
    return Settings(
        deepseek_api_key="fake-key",
        bot_token="fake-token",
        channel_id="fake-channel",
        deepseek_model="deepseek-chat",
        rss_urls=["http://test.rss"],
        db_path=str(tmp_path / "test.db"),
        max_news_per_run=2,
    )

@patch("market_voice_bot.main.time.sleep")
@patch("market_voice_bot.main.TelegramClient")
@patch("market_voice_bot.main.AIWriter")
@patch("market_voice_bot.main.Storage")
@patch("market_voice_bot.main.fetch_all_entries")
def test_run_success(mock_fetch, mock_storage_class, mock_ai_class, mock_tg_class, mock_sleep, mock_settings):
    # Имитируем получение одной новой новости
    mock_fetch.return_value = [NewsEntry("Title 1", "http://link1", "Sum 1", None)]
    
    mock_storage = MagicMock()
    mock_storage.is_posted.return_value = False
    mock_storage_class.return_value = mock_storage
    
    mock_writer = MagicMock()
    mock_writer.generate_post.return_value = "Текст поста"
    mock_ai_class.return_value = mock_writer
    
    mock_telegram = MagicMock()
    mock_tg_class.return_value = mock_telegram

    # Запускаем основной процесс
    run(mock_settings)

    # Проверяем, что пост был отправлен и отмечен как опубликованный
    mock_telegram.send_message.assert_called_once_with("Текст поста\n\nДжерело: http://link1")
    mock_storage.mark_posted.assert_called_once_with("http://link1", "Title 1")
