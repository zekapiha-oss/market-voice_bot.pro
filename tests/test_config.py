import os
import pytest
from market_voice_bot.config import Settings, ConfigError, DEFAULT_MODEL

def test_from_env_success(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setenv("BOT_TOKEN", "test-bot-token")
    monkeypatch.setenv("CHANNEL_ID", "test-channel")
    
    settings = Settings.from_env()
    
    assert settings.deepseek_api_key == "test-deepseek-key"
    assert settings.bot_token == "test-bot-token"
    assert settings.channel_id == "test-channel"
    assert settings.deepseek_model == DEFAULT_MODEL

def test_from_env_missing_vars(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("CHANNEL_ID", raising=False)
    
    with pytest.raises(ConfigError):
        Settings.from_env()
