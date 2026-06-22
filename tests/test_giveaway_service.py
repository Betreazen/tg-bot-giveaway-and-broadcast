"""Tests for winner selection logic (DB repos mocked)."""

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import bot.services.giveaway_service as gs
from bot.services.giveaway_service import (
    NoParticipantsError,
    format_winner_list,
    select_winners,
)


def _participants(n: int):
    return [SimpleNamespace(user_id=i, username_snapshot=f"user{i}") for i in range(n)]


def _giveaway(num_winners: int, ended_at=None):
    return SimpleNamespace(
        id=1,
        num_winners=num_winners,
        ended_at=ended_at,
        end_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.mark.asyncio
async def test_select_winners_picks_requested_count(monkeypatch):
    monkeypatch.setattr(
        gs.participant_repo, "get_participants", AsyncMock(return_value=_participants(10))
    )
    captured = {}

    async def fake_add_winners(**kwargs):
        captured.update(kwargs)
        return [object() for _ in kwargs["user_ids"]]

    monkeypatch.setattr(gs.winner_repo, "add_winners", AsyncMock(side_effect=fake_add_winners))

    winners = await select_winners(session=None, giveaway=_giveaway(3))

    assert len(winners) == 3
    assert len(captured["user_ids"]) == 3
    assert len(set(captured["user_ids"])) == 3  # no duplicates


@pytest.mark.asyncio
async def test_select_winners_caps_at_participant_count(monkeypatch):
    monkeypatch.setattr(
        gs.participant_repo, "get_participants", AsyncMock(return_value=_participants(2))
    )

    async def fake_add_winners(**kwargs):
        return [object() for _ in kwargs["user_ids"]]

    monkeypatch.setattr(gs.winner_repo, "add_winners", AsyncMock(side_effect=fake_add_winners))

    winners = await select_winners(session=None, giveaway=_giveaway(5))
    assert len(winners) == 2


@pytest.mark.asyncio
async def test_select_winners_uses_ended_at_snapshot(monkeypatch):
    ended = datetime(2024, 5, 5, tzinfo=UTC)
    monkeypatch.setattr(
        gs.participant_repo, "get_participants", AsyncMock(return_value=_participants(1))
    )
    captured = {}

    async def fake_add_winners(**kwargs):
        captured.update(kwargs)
        return [object()]

    monkeypatch.setattr(gs.winner_repo, "add_winners", AsyncMock(side_effect=fake_add_winners))

    await select_winners(session=None, giveaway=_giveaway(1, ended_at=ended))
    assert captured["giveaway_end_snapshot"] == ended


@pytest.mark.asyncio
async def test_select_winners_no_participants_raises(monkeypatch):
    monkeypatch.setattr(gs.participant_repo, "get_participants", AsyncMock(return_value=[]))
    with pytest.raises(NoParticipantsError):
        await select_winners(session=None, giveaway=_giveaway(1))


def test_format_winner_list_with_and_without_username():
    winners = [
        SimpleNamespace(username_snapshot="alice", user_id=1),
        SimpleNamespace(username_snapshot=None, user_id=2),
    ]
    out = format_winner_list(winners)
    assert "1. @alice" in out
    assert "2. ID: 2" in out


def test_format_winner_list_empty():
    assert format_winner_list([]) == "No winners"
