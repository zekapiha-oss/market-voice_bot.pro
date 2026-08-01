from unittest.mock import MagicMock, patch

from market_voice_bot.rss_fetcher import (
    NewsEntry,
    fetch_all_entries,
    fetch_entries,
    sort_by_date_ascending,
)


def _make_feed(entries, bozo=False):
    feed = MagicMock()
    feed.bozo = bozo
    feed.entries = entries
    feed.get.return_value = "parse error"
    return feed


def _make_entry(title, link, summary="", published_parsed=None):
    entry = MagicMock()
    entry.title = title
    entry.link = link
    entry.summary = summary
    entry.published_parsed = published_parsed
    return entry


@patch("market_voice_bot.rss_fetcher.feedparser.parse")
def test_fetch_entries_returns_parsed_news(mock_parse):
    mock_parse.return_value = _make_feed([_make_entry("Title", "https://a.com/1", "Summary")])

    entries = fetch_entries("https://feed.com/rss")

    assert len(entries) == 1
    assert entries[0].title == "Title"
    assert entries[0].link == "https://a.com/1"
    assert entries[0].summary == "Summary"


@patch("market_voice_bot.rss_fetcher.feedparser.parse")
def test_fetch_entries_discards_entries_without_link(mock_parse):
    mock_parse.return_value = _make_feed(
        [_make_entry("No link", ""), _make_entry("Has link", "https://a.com/2")]
    )

    entries = fetch_entries("https://feed.com/rss")

    assert len(entries) == 1
    assert entries[0].link == "https://a.com/2"


@patch("market_voice_bot.rss_fetcher.feedparser.parse")
def test_fetch_entries_returns_empty_on_broken_feed(mock_parse):
    mock_parse.return_value = _make_feed([], bozo=True)

    entries = fetch_entries("https://broken-feed.com/rss")

    assert entries == []


@patch("market_voice_bot.rss_fetcher.feedparser.parse")
def test_fetch_entries_never_raises_on_network_error(mock_parse):
    mock_parse.side_effect = Exception("network down")

    entries = fetch_entries("https://feed.com/rss")

    assert entries == []


@patch("market_voice_bot.rss_fetcher.fetch_entries")
def test_fetch_all_entries_combines_multiple_feeds(mock_fetch):
    mock_fetch.side_effect = [
        [NewsEntry("A", "l1", "")],
        [NewsEntry("B", "l2", "")],
    ]

    entries = fetch_all_entries(["https://feed1.com", "https://feed2.com"])

    assert len(entries) == 2
    assert mock_fetch.call_count == 2


def test_sort_by_date_ascending_orders_oldest_first():
    older = NewsEntry("A", "l1", "", (2024, 1, 1, 0, 0, 0, 0, 0, 0))
    newer = NewsEntry("B", "l2", "", (2024, 1, 2, 0, 0, 0, 0, 0, 0))

    result = sort_by_date_ascending([newer, older])

    assert result == [older, newer]


def test_sort_by_date_ascending_handles_missing_dates():
    no_date = NewsEntry("A", "l1", "", ())
    with_date = NewsEntry("B", "l2", "", (2024, 1, 1, 0, 0, 0, 0, 0, 0))

    result = sort_by_date_ascending([with_date, no_date])

    assert result == [no_date, with_date]
