"""
Episode Engine.

Creates and stores episodic memories from completed conversations.
"""

from __future__ import annotations

from src.cognition.conversation import Conversation
from src.cognition.episode import Episode
from src.cognition.episode_builder import EpisodeBuilder
from src.cognition.episode_repository import EpisodeRepository


class EpisodeEngine:
    """
    Handles episodic memory creation and persistence.

    The engine converts a completed Conversation into an Episode
    and stores it in the EpisodeRepository.
    """

    def __init__(
        self,
        builder: EpisodeBuilder,
        repository: EpisodeRepository,
    ) -> None:

        self.builder = builder
        self.repository = repository

    def remember(
        self,
        conversation: Conversation,
    ) -> Episode:
        """
        Build an Episode from a Conversation and store it.
        """

        episode = self.builder.build(conversation)

        self.repository.add_episode(episode)

        return episode