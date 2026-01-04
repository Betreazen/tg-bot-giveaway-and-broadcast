"""Giveaway business logic service."""

import logging
import random

from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Giveaway, Participant, Winner
from bot.db.repo import participant_repo, winner_repo

logger = logging.getLogger(__name__)


class NoParticipantsError(Exception):
    """Raised when trying to select winners but no participants exist."""

    pass


async def select_winners(session: AsyncSession, giveaway: Giveaway) -> list[Winner]:
    """
    Select random winners for a giveaway.

    Args:
        session: Database session
        giveaway: Giveaway object

    Returns:
        List of Winner objects

    Raises:
        NoParticipantsError: If no participants in giveaway
    """
    # Get all participants
    participants = await participant_repo.get_participants(session, giveaway.id)

    if not participants:
        raise NoParticipantsError(f"No participants in giveaway {giveaway.id}")

    # Determine number of winners
    num_winners = min(giveaway.num_winners, len(participants))

    # Randomly select winners
    selected_participants: list[Participant] = random.sample(participants, num_winners)

    logger.info(
        f"Selected {num_winners} winners from {len(participants)} participants for giveaway {giveaway.id}"
    )

    # Prepare winner data
    user_ids = [p.user_id for p in selected_participants]
    username_snapshots = {p.user_id: p.username_snapshot for p in selected_participants}

    # Use ended_at if available, otherwise end_at
    giveaway_end_snapshot = giveaway.ended_at if giveaway.ended_at else giveaway.end_at

    # Create winner records
    winners = await winner_repo.add_winners(
        session=session,
        giveaway_id=giveaway.id,
        user_ids=user_ids,
        username_snapshots=username_snapshots,
        giveaway_end_snapshot=giveaway_end_snapshot,
    )

    logger.info(f"Created {len(winners)} winner records for giveaway {giveaway.id}")

    return winners


def format_winner_list(winners: list[Winner]) -> str:
    """
    Format list of winners for display.

    Args:
        winners: List of Winner objects

    Returns:
        Formatted string with winner list
    """
    if not winners:
        return "No winners"

    lines = []
    for idx, winner in enumerate(winners, 1):
        username = f"@{winner.username_snapshot}" if winner.username_snapshot else f"ID: {winner.user_id}"
        lines.append(f"{idx}. {username}")

    return "\n".join(lines)
