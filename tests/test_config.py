import pytest

from market_voice_bot.config import ConfigError, Settings


@pytest.fixture
def required_env(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")
    monkeypatch.setenv("BOT_TOKEN", "bot-token")
    monkeypatch.setenv("CHANNEL_ID", "@channel")


def test_from_env_reads_required_fields(required_env):
    settings = Settings.from_env()

    assert settings.groq_api_key == "groq-key"
    assert settings.bot_token == "bot-token"
    assert settings.channel_id == "@channel"


def test_from_env_uses_defaults_when_optional_vars_missing(required_env):
    settings = Settings.from_env()

    assert settings.groq_model == "llama-3.1-8b-instant"
    assert settings.max_news_per_run == 5
    assert settings.db_path == "data/state.db"
    assert len(settings.rss_urls) > 0


def test_from_env_raises_when_required_var_missing(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("CHANNEL_ID", raising=False)

    with pytest.raises(ConfigError):
        Settings.from_env()


def test_from_env_parses_custom_rss_urls(required_env, monkeypatch):
    monkeypatch.setenv("RSS_URLS", "https://a.com/rss, https://b.com/rss")

    settings = Settings.from_env()

    assert settings.rss_urls == ["https://a.com/rss", "https://b.com/rss"]


def test_from_env_raises_on_non_numeric_max_news(required_env, monkeypatch):
    monkeypatch.setenv("MAX_NEWS_PER_RUN", "not-a-number")

    with pytest.raises(ConfigError):
        Settings.from_env()
