from src.conversation.conversation_models import InteractionType
from src.interaction.events import PresenceEvent


class InteractionClassifier:
    """
    Classifies interaction intent from presence events and cognitive context.
    """

    def classify(
        self,
        event: PresenceEvent,
        assistance_level: int = 0,
        has_relationship: bool = False,
        has_goals: bool = False,
    ) -> InteractionType:
        if assistance_level >= 5:
            return InteractionType.SAFETY
        if has_relationship or (event.relationship and "unknown" not in event.relationship.lower()):
            return InteractionType.RELATIONSHIP
        if event.name:
            return InteractionType.GREETING
        if has_goals:
            return InteractionType.REMINDER
        return InteractionType.CASUAL
