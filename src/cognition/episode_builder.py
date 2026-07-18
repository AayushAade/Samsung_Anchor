"""
Episode Builder.

Constructs Episode objects from Conversations.
"""

from __future__ import annotations

from src.cognition.conversation import Conversation
from src.cognition.episode import Episode


class EpisodeBuilder:
    """
    Converts a Conversation into an Episode.
    """

    def build(
        self,
        conversation: Conversation,
    ) -> Episode:
        """
        Build an Episode from a completed Conversation.
        """

        return Episode(
            person=conversation.person,
            summary=conversation.summary or conversation.transcript,
            location=conversation.location,
            commitments=conversation.commitments,
            tags=conversation.tags,
            timestamp=conversation.timestamp,
        )