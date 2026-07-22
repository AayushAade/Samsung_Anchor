from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from src.conversation.conversation_models import InteractionType, ResponseStrategy, SpeakerRole


@dataclass
class ConversationTurnLog:
    """
    Privacy-first structured conversation turn record.
    """

    timestamp: datetime
    speaker: SpeakerRole
    intent: InteractionType
    strategy: ResponseStrategy
    summary: str


class ConversationHistory:
    """
    Maintains lightweight, privacy-first turn history.
    """

    def __init__(self, max_turns: int = 50) -> None:
        self.max_turns = max_turns
        self._history: List[ConversationTurnLog] = []

    def log_turn(
        self,
        speaker: SpeakerRole,
        intent: InteractionType,
        strategy: ResponseStrategy,
        summary: str,
    ) -> ConversationTurnLog:
        turn = ConversationTurnLog(
            timestamp=datetime.now(),
            speaker=speaker,
            intent=intent,
            strategy=strategy,
            summary=summary[:100] if summary else "",
        )
        self._history.append(turn)
        if len(self._history) > self.max_turns:
            self._history.pop(0)
        return turn

    def get_recent_turns(self, limit: int = 5) -> List[ConversationTurnLog]:
        return self._history[-limit:]

    def clear(self) -> None:
        self._history.clear()
