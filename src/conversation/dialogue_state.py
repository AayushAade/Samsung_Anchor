import time
from typing import Optional
from src.conversation.conversation_models import ConversationState


class DialogueTracker:
    """
    Tracks state machine transitions, conversation duration, topic, and turn metrics.
    """

    def __init__(self) -> None:
        self.state: ConversationState = ConversationState.IDLE
        self.turn_count: int = 0
        self.start_time: Optional[float] = None
        self.topic: str = "Daily Routine & Orientation"
        self.owner: str = "Patient"

    def start_conversation(self, topic: str = "Daily Routine & Orientation", owner: str = "Patient") -> None:
        self.state = ConversationState.GREETING
        self.turn_count = 0
        self.start_time = time.perf_counter()
        self.topic = topic
        self.owner = owner

    def transition_to(self, new_state: ConversationState, topic: Optional[str] = None) -> None:
        self.state = new_state
        if topic:
            self.topic = topic

    def increment_turn(self) -> int:
        self.turn_count += 1
        return self.turn_count

    def end_conversation(self) -> None:
        self.state = ConversationState.CONVERSATION_END

    def get_elapsed_seconds(self) -> float:
        if self.start_time is None:
            return 0.0
        return round(time.perf_counter() - self.start_time, 1)

    def reset(self) -> None:
        self.state = ConversationState.IDLE
        self.turn_count = 0
        self.start_time = None
        self.topic = "Daily Routine & Orientation"
        self.owner = "Patient"
