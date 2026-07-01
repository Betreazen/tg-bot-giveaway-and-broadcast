"""Tests for the suspicious-list pagination helper."""

from bot.handlers.admin.suspicious import _paginate


def test_single_page_when_short():
    lines = [f"{i}. @user{i}" for i in range(5)]
    pages = _paginate("HEAD\n\n", lines)
    assert len(pages) == 1
    for line in lines:
        assert line in pages[0]


def test_empty_lines_returns_header():
    pages = _paginate("HEAD", [])
    assert pages == ["HEAD"]


def test_splits_into_multiple_pages_under_limit():
    lines = [f"{i}. @some_long_username_{i}" for i in range(1000)]
    pages = _paginate("HEAD\n\n", lines, limit=1000)
    assert len(pages) > 1
    assert all(len(p) <= 1000 for p in pages)
    # every line ends up in exactly one page
    joined = "\n".join(pages)
    for line in lines:
        assert line in joined
