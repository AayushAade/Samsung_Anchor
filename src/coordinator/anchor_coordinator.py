"""
Anchor Coordinator

This module contains the central orchestration layer of Samsung Anchor.

The Coordinator is responsible for coordinating communication between
independent subsystems while keeping them loosely coupled.

It owns application flow, but does not implement the internal logic of
Vision, Audio, Memory, or Reasoning.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from src.integration.identity_learning_pipeline import (
    process_identity_learning,
)

from src.integration.async_identity_learning import (
    start_identity_learning,
)

from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.interaction.actions import InteractionAction

# ------------------------------------------------------------------
# Import subsystem types ONLY for static type checking.
# ------------------------------------------------------------------

if TYPE_CHECKING:
    from src.memory.database import MemoraDatabase
    from src.vision.face_recognizer import MemoraFaceRecognizer
    from src.audio.audio_listener import MemoraAudioListener
    from src.reasoning.context_binder import MemoraContextBinder


class AnchorCoordinator:
    """
    Central orchestration layer for Samsung Anchor.

    The Coordinator owns application flow while delegating all
    subsystem-specific logic to the corresponding modules.
    """

    def __init__(
        self,
        database: "MemoraDatabase",
        recognizer: "MemoraFaceRecognizer",
        listener: "MemoraAudioListener",
        binder: "MemoraContextBinder",
        speaker: Any,
    ) -> None:
        """
        Initialize the coordinator with subsystem instances.
        """

        self.database = database
        self.recognizer = recognizer
        self.listener = listener
        self.binder = binder
        self.speaker = speaker

        # Runtime state
        self.running = False

        self.visible_faces = set()
        self.visible_objects = set()

        # ------------------------------------------------------
        # Cognitive Pipeline
        # ------------------------------------------------------

        self.pipeline = CognitivePipeline()

        self._pending_actions: list[InteractionAction] = []

        # Faces currently undergoing identity learning.
        self._learning_faces: set[str] = set()

        # Last learning attempt for each face.
        self._last_learning_attempt: dict[str, float] = {}

        # Seconds before asking again.
        self._learning_cooldown = 10.0

    # ==========================================================
    # Lifecycle
    # ==========================================================

    def initialize(self) -> None:
        """
        Prepare the coordinator for execution.
        """

        self.running = False
        self._pending_actions.clear()
        self.pipeline.reset()

    def start(self) -> None:
        """
        Start coordinator execution.
        """

        self.running = True

    def shutdown(self) -> None:
        """
        Gracefully stop coordinator execution.
        """

        self.running = False

    # ==========================================================
    # Vision Pipeline
    # ==========================================================

    def process_frame(self, frame):
        """
        Process a single frame through the Vision subsystem.

        Recognition results are passed through the cognitive
        pipeline to generate interaction actions.
        """

        results = self.recognizer.process_frame(
            frame,
            self.database,
        )

        iterable = [results] if isinstance(results, dict) else results

        self._pending_actions.clear()

        for result in iterable:

            # Existing cognitive pipeline
            self._pending_actions.extend(
                self.pipeline.process(result)
            )

            # Trigger identity learning for unknown people
            face_id = result.get("face_id")
            name = result.get("name")

            if (
    face_id
    and name is None
    and self._can_start_learning(face_id)
):
                self.start_identity_learning(face_id)

        return results

    def consume_actions(self) -> list[InteractionAction]:
        """
        Return pending interaction actions.

        Calling this method also clears the queue.
        """

        actions = list(self._pending_actions)
        self._pending_actions.clear()

        return actions


    def _can_start_learning(
    self,
    face_id: str,
) -> bool:
        """
        Returns True if identity learning may begin.
        """

        if face_id in self._learning_faces:
            return False

        last = self._last_learning_attempt.get(face_id)

        if last is None:
            return True

        import time

        return (time.time() - last) >= self._learning_cooldown

    # ==========================================================
    # Live Identity Learning
    # ==========================================================

    def start_identity_learning(
        self,
        face_id: str,
    ) -> bool:
        """
        Start background identity learning for an unknown face.

        Returns
        -------
        bool
            True if learning was started.
        """

        if not face_id:
            return False

        if face_id in self._learning_faces:
            return False

        self._learning_faces.add(face_id)

        import time
        self._last_learning_attempt[face_id] = time.time()

        def finished(
            finished_face_id: str,
            result: dict,
        ) -> None:

            self._learning_faces.discard(
                finished_face_id
            )

            print(
                f"\n🧠 Identity Learning Finished:"
                f" {result}"
            )

        start_identity_learning(
            face_id=face_id,
            listener=self.listener,
            binder=self.binder,
            database=self.database,
            speaker=self.speaker,
            on_finished=finished,
        )

        return True

    # ==========================================================
    # Identity Learning Pipeline
    # ==========================================================

    def process_transcript(
        self,
        face_id: str,
        transcript: str,
    ):
        """
        Process a transcript associated with a detected face.

        Delegates identity learning to the Integration layer.
        """

        return process_identity_learning(
            face_id=face_id,
            transcript=transcript,
            database=self.database,
            binder=self.binder,
        )