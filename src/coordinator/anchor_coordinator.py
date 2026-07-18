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
import threading
import queue
from typing import TYPE_CHECKING, Any

from src.integration.identity_learning_pipeline import (
    process_identity_learning,
)

from src.integration.async_identity_learning import (
    start_identity_learning,
)

from src.pipeline.cognitive_pipeline import CognitivePipeline
from src.interaction.actions import InteractionAction
from src.core.event_bus import EventBus
from src.cognition.cognitive_memory_manager import CognitiveMemoryManager
from src.llm.reasoning_client import MockReasoningClient

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
        # Event Bus & Asynchronous Decoupling
        # ------------------------------------------------------
        
        self.event_bus = EventBus()
        self._cognitive_queue = queue.Queue()
        self._action_queue = queue.Queue()
        
        self.event_bus.subscribe("face_detected", self._on_face_detected)

        # ------------------------------------------------------
        # Cognitive Pipeline & Memory Manager
        # ------------------------------------------------------

        self.pipeline = CognitivePipeline(self.database)
        self.memory_manager = CognitiveMemoryManager(self.database.SessionFactory, MockReasoningClient())

        self._cognitive_thread = None

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
        while not self._action_queue.empty():
            self._action_queue.get_nowait()
        while not self._cognitive_queue.empty():
            self._cognitive_queue.get_nowait()
        self.pipeline.reset()

    def start(self) -> None:
        """
        Start coordinator execution.
        """
        self.running = True
        self._cognitive_thread = threading.Thread(target=self._cognitive_worker_loop, daemon=True)
        self._cognitive_thread.start()

    def shutdown(self) -> None:
        """
        Gracefully stop coordinator execution.
        """
        self.running = False
        if self._cognitive_thread is not None:
            self._cognitive_thread.join(timeout=2.0)
        self.memory_manager.shutdown()

    # ==========================================================
    # Event Handlers & Workers
    # ==========================================================

    def _on_face_detected(self, result: dict):
        """Callback from EventBus. Pushes to worker queue."""
        self._cognitive_queue.put(result)

    def _cognitive_worker_loop(self):
        """
        Background thread pulling from cognitive queue, running 
        the pipeline, and putting actions into the action queue.
        This ensures camera frames are never dropped due to slow reasoning.
        """
        while self.running:
            try:
                # Wait for an event with timeout to allow graceful shutdown
                result = self._cognitive_queue.get(timeout=0.1)
                
                actions = self.pipeline.process(result)
                for action in actions:
                    self._action_queue.put(action)
                    
            except queue.Empty:
                continue
            except Exception as e:
                import traceback
                print(f"[Coordinator Error] Cognitive Worker failed: {e}")
                traceback.print_exc()

    # ==========================================================
    # Vision Pipeline
    # ==========================================================

    def process_frame(self, frame):
        """
        Process a single frame through the Vision subsystem.

        Recognition results are published to the EventBus, completely
        decoupling the synchronous camera loop from the heavy
        cognitive processing.
        """

        results = self.recognizer.process_frame(
            frame,
            self.database,
        )

        iterable = [results] if isinstance(results, dict) else results

        for result in iterable:
            # Publish to event bus instead of calling synchronously
            self.event_bus.publish("face_detected", result)

            # Trigger identity learning for unknown people (still handled async)
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
        actions = []
        while not self._action_queue.empty():
            try:
                actions.append(self._action_queue.get_nowait())
            except queue.Empty:
                break
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
            memory_manager=self.memory_manager,
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