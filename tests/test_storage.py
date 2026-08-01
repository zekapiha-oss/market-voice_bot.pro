import pytest

from market_voice_bot.storage import Storage


@pytest.fixture
def storage(tmp_path):
    db_path = tmp_path / "test_state.db"
    return Storage(str(db_path))


def test_new_link_is_not_posted(storage):
    assert storage.is_posted("https://example.com/a") is False


def test_mark_posted_makes_link_visible(storage):
    storage.mark_posted("https://example.com/a", "Title A")
    assert storage.is_posted("https://example.com/a") is True


def test_mark_posted_is_idempotent(storage):
    storage.mark_posted("https://example.com/a", "Title A")
    storage.mark_posted("https://example.com/a", "Title A (updated)")
    assert storage.count() == 1


def test_creates_db_file_and_parent_dirs(tmp_path):
    nested_path = tmp_path / "nested" / "dir" / "state.db"
    Storage(str(nested_path))
    assert nested_path.exists()


def test_prune_keeps_only_last_n(storage):
    for i in range(5):
        storage.mark_posted(f"https://example.com/{i}", f"Title {i}")
    assert storage.count() == 5

    storage.prune(keep_last=2)
    assert storage.count() == 2


def test_persists_across_instances(tmp_path):
    db_path = str(tmp_path / "state.db")
    Storage(db_path).mark_posted("https://example.com/a", "Title A")

    reopened = Storage(db_path)
    assert reopened.is_posted("https://example.com/a") is True
