from src.conversation.conversation_models import InteractionType, ResponseStrategy
from src.interaction.events import PresenceEvent


class ResponsePlanner:
    """
    Response Planner determining HOW responses should be delivered.
    The planner selects the strategy; the LLM generates the language.
    """

    def plan_strategy(
        self,
        event: PresenceEvent,
        assistance_level: int = 0,
        attention_should_interrupt: bool = False,
        interaction_type: InteractionType = InteractionType.CASUAL,
    ) -> ResponseStrategy:
        if assistance_level >= 5:
            return ResponseStrategy.SAFETY_ALERT
        if interaction_type == InteractionType.GREETING:
            return ResponseStrategy.GREETING
        if interaction_type == InteractionType.RELATIONSHIP:
            return ResponseStrategy.RELATIONSHIP_CUE
        if attention_should_interrupt:
            return ResponseStrategy.CONTEXT_RESTORATION
        if assistance_level == 1:
            return ResponseStrategy.ENCOURAGEMENT
        if assistance_level == 2:
            return ResponseStrategy.REMINDER

        return ResponseStrategy.SUPPORTIVE_SILENCE
