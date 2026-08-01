from unittest.mock import MagicMock, patch

import pytest

from market_voice_bot.ai_writer import AIGenerationError, AIWriter
from market_voice_bot.rss_fetcher import NewsEntry


def _make_completion(text):
    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content=text))]
    return completion


@patch("market_voice_bot.ai_writer.Groq")
def test_generate_post_returns_model_text(mock_groq_cls):
    client = MagicMock()
    client.chat.completions.create.return_value = _make_completion("📊 Пост про крипту")
    mock_groq_cls.return_value = client

    writer = AIWriter(api_key="x", model="m")
    news = NewsEntry("Title", "link", "summary")

    result = writer.generate_post(news)

    assert result == "📊 Пост про крипту"


@patch("market_voice_bot.ai_writer.Groq")
def test_generate_post_returns_none_on_skip(mock_groq_cls):
    client = MagicMock()
    client.chat.completions.create.return_value = _make_completion("SKIP")
    mock_groq_cls.return_value = client

    writer = AIWriter(api_key="x", model="m")
    news = NewsEntry("Title", "link", "summary")

    result = writer.generate_post(news)

    assert result is None


@patch("market_voice_bot.ai_writer.Groq")
def test_generate_post_treats_skip_case_insensitively(mock_groq_cls):
    client = MagicMock()
    client.chat.completions.create.return_value = _make_completion("  skip  ")
    mock_groq_cls.return_value = client

    writer = AIWriter(api_key="x", model="m")
    news = NewsEntry("Title", "link", "summary")

    assert writer.generate_post(news) is None


@patch("market_voice_bot.ai_writer.time.sleep", return_value=None)
@patch("market_voice_bot.ai_writer.Groq")
def test_generate_post_raises_after_all_retries_fail(mock_groq_cls, mock_sleep):
    client = MagicMock()
    client.chat.completions.create.side_effect = Exception("API down")
    mock_groq_cls.return_value = client

    writer = AIWriter(api_key="x", model="m")
    news = NewsEntry("Title", "link", "summary")

    with pytest.raises(AIGenerationError):
        writer.generate_post(news)

    assert client.chat.completions.create.call_count == 3


@patch("market_voice_bot.ai_writer.time.sleep", return_value=None)
@patch("market_voice_bot.ai_writer.Groq")
def test_generate_post_succeeds_after_transient_failure(mock_groq_cls, mock_sleep):
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        Exception("timeout"),
        _make_completion("Пост після повтору"),
    ]
    mock_groq_cls.return_value = client

    writer = AIWriter(api_key="x", model="m")
    news = NewsEntry("Title", "link", "summary")

    result = writer.generate_post(news)

    assert result == "Пост після повтору"
