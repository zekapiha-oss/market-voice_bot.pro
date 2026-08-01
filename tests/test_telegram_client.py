from unittest.mock import MagicMock, patch

import pytest

from market_voice_bot.telegram_client import (
    TELEGRAM_MESSAGE_LIMIT,
    TelegramClient,
    TelegramSendError,
)


@patch("market_voice_bot.telegram_client.requests.post")
def test_send_message_success(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    client = TelegramClient("token", "chat_id")

    client.send_message("hello")

    mock_post.assert_called_once()


@patch("market_voice_bot.telegram_client.time.sleep", return_value=None)
@patch("market_voice_bot.telegram_client.requests.post")
def test_send_message_retries_on_rate_limit(mock_post, mock_sleep):
    rate_limited = MagicMock(status_code=429)
    rate_limited.json.return_value = {"parameters": {"retry_after": 1}}
    ok = MagicMock(status_code=200)
    mock_post.side_effect = [rate_limited, ok]

    client = TelegramClient("token", "chat_id")
    client.send_message("hello")

    assert mock_post.call_count == 2
    mock_sleep.assert_called_once_with(1)


@patch("market_voice_bot.telegram_client.time.sleep", return_value=None)
@patch("market_voice_bot.telegram_client.requests.post")
def test_send_message_raises_after_all_retries_fail(mock_post, mock_sleep):
    mock_post.return_value = MagicMock(status_code=500, text="internal error")
    client = TelegramClient("token", "chat_id")

    with pytest.raises(TelegramSendError):
        client.send_message("hello")

    assert mock_post.call_count == 3


@patch("market_voice_bot.telegram_client.requests.post")
def test_send_message_truncates_text_over_limit(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    client = TelegramClient("token", "chat_id")

    client.send_message("a" * 5000)

    sent_payload = mock_post.call_args.kwargs["json"]
    assert len(sent_payload["text"]) <= TELEGRAM_MESSAGE_LIMIT


@patch("market_voice_bot.telegram_client.requests.post")
def test_send_message_uses_configured_chat_id(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    client = TelegramClient("token", "my_channel")

    client.send_message("hello")

    sent_payload = mock_post.call_args.kwargs["json"]
    assert sent_payload["chat_id"] == "my_channel"
