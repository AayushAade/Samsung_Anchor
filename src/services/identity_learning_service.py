"""
Identity Learning Service.

Coordinates identity learning and episodic memory creation.
"""

from __future__ import annotations

from src.cognition.conversation import Conversation
from src.cognition.episode_builder import EpisodeBuilder
from src.cognition.episode_engine import EpisodeEngine
from src.cognition.episode_repository import EpisodeRepository
from src.integration.identity_learning_pipeline import (
    process_identity_learning,
)


class IdentityLearningService:
    """
    High-level workflow for identity learning.

    Responsibilities:
        1. Learn a person's identity.
        2. Create a Conversation.
        3. Store an Episode.
    """

    def __init__(self) -> None:

        self.episode_engine = EpisodeEngine(
            builder=EpisodeBuilder(),
            repository=EpisodeRepository(),
        )

    def process(
        self,
        *,
        face_id: str,
        transcript: str,
        database,
        binder,
    ) -> dict:
        """
        Execute the complete identity-learning workflow.
        """

        result = process_identity_learning(
            face_id=face_id,
            transcript=transcript,
            database=database,
            binder=binder,
        )

        if (
            result.get("success")
            and result.get("is_confirmed")
        ):

            conversation = Conversation(
                person=result["name"],
                transcript=transcript,
            )

            self.episode_engine.remember(
                conversation
            )

        return result