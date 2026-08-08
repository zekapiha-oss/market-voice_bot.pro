import pytest
from unittest.mock import patch, MagicMock
from market_voice_bot.ai_writer import AIWriter, AIGenerationError, SKIP_MARKER
from market_voice_bot.rss_fetcher import NewsEntry

@pytest.fixture
def news_entry():
    return NewsEntry(
        title="Тестовая новость",
        link="http://example.com",
        summary="Описание тестовой новости.",
        published_parsed=None,
    )

@patch("market_voice_bot.ai_writer.OpenAI")
def test_generate_post_success(mock_openai_class, news_entry):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Сгенерированный текст поста"

    writer = AIWriter("fake-key", "deepseek-chat")
    result = writer.generate_post(news_entry)

    assert result == "Сгенерированный текст поста"
    mock_client.chat.completions.create.assert_called_once()

@patch("market_voice_bot.ai_writer.OpenAI")
def test_generate_post_skip(mock_openai_class, news_entry):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = SKIP_MARKER

    writer = AIWriter("fake-key", "deepseek-chat")
    result = writer.generate_post(news_entry)

    assert result is None

@patch("market_voice_bot.ai_writer.time.sleep")
@patch("market_voice_bot.ai_writer.OpenAI")
def test_generate_post_raises_error_after_retries(mock_openai_class, mock_sleep, news_entry):
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    # Имитируем ошибку API при каждом вызове
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    writer = AIWriter("fake-key", "deepseek-chat")
    with pytest.raises(AIGenerationError):
        writer.generate_post(news_entry)
