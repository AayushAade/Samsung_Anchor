from typing import Optional, Any
from src.conversation.conversation_history import ConversationHistory
from src.conversation.conversation_models import (
    ConversationContext,
    ConversationState,
    InteractionType,
    ResponseStrategy,
    SpeakerRole,
)
from src.conversation.conversation_policy import ConversationPolicy
from src.conversation.dialogue_state import DialogueTracker
from src.conversation.interaction_classifier import InteractionClassifier
from src.conversation.response_planner import ResponsePlanner
from src.conversation.turn_manager import TurnManager
from src.interaction.events import PresenceEvent


class ConversationManager:
    """
    Main orchestrator for the Human-Centered Conversation Engine.
    Consumes cognitive pipeline outputs and drives calm, context-aware dialogue behavior.
    """

    def __init__(self) -> None:
        self.dialogue_tracker = DialogueTracker()
        self.turn_manager = TurnManager()
        self.policy = ConversationPolicy()
        self.classifier = InteractionClassifier()
        self.planner = ResponsePlanner()
        self.history = ConversationHistory()

    def process_cycle(
        self,
        event: PresenceEvent,
        cognitive_context: Optional[Any] = None,
        attention_should_interrupt: bool = False,
    ) -> ConversationContext:
        """
        Executes one conversation cycle and yields updated ConversationContext.
        """
        # 1. Active Speaker Determination
        speaker = self.turn_manager.determine_speaker_from_event(event)

        # 2. Extract Cognitive Parameters
        assistance_level = 0
        has_relationship = False
        has_goals = False

        if cognitive_context:
            if getattr(cognitive_context, "assistance", None):
                assistance_level = getattr(cognitive_context.assistance, "level_code", 0)
            if getattr(cognitive_context, "social", None) and getattr(cognitive_context.social, "active_profile", None):
                has_relationship = True

        # 3. Intent Classification
        intent = self.classifier.classify(
            event=event,
            assistance_level=assistance_level,
            has_relationship=has_relationship,
            has_goals=has_goals,
        )

        # 4. State Machine Transition
        if self.dialogue_tracker.state == ConversationState.IDLE:
            topic = f"Visit with {event.name}" if event.name else "Daily Routine & Orientation"
            self.dialogue_tracker.start_conversation(topic=topic, owner="Patient")

        new_state, strategy = self.policy.evaluate_policy(
            event=event,
            active_speaker=speaker,
            current_state=self.dialogue_tracker.state,
            assistance_level=assistance_level,
            attention_should_interrupt=attention_should_interrupt,
        )
        self.dialogue_tracker.transition_to(new_state)
        self.dialogue_tracker.increment_turn()

        # 5. Response Strategy Planning
        if strategy == ResponseStrategy.SUPPORTIVE_SILENCE:
            strategy = self.planner.plan_strategy(
                event=event,
                assistance_level=assistance_level,
                attention_should_interrupt=attention_should_interrupt,
                interaction_type=intent,
            )

        # 6. History Logging
        self.history.log_turn(
            speaker=speaker,
            intent=intent,
            strategy=strategy,
            summary=f"{speaker.value} turn in state {new_state.value}",
        )

        return ConversationContext(
            state=self.dialogue_tracker.state,
            active_speaker=speaker,
            response_strategy=strategy,
            interaction_type=intent,
            turn_count=self.dialogue_tracker.turn_count,
            elapsed_seconds=self.dialogue_tracker.get_elapsed_seconds(),
            topic=self.dialogue_tracker.topic,
            owner=self.dialogue_tracker.owner,
        )

    def reset(self) -> None:
        self.dialogue_tracker.reset()
