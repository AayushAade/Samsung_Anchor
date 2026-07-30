from src.conversation.conversation_models import InteractionType, ResponseStrategy
from src.conversation.response_planner import ResponsePlanner
from src.interaction.events import PresenceEvent, PresenceEventType


def test_response_planner_strategies():
    planner = ResponsePlanner()
    event = PresenceEvent(
        type=PresenceEventType.PERSON_ARRIVED,
        face_id="Face_1",
        name="Sarah",
        relationship="Daughter",
    )

    # 1. Safety Alert
    strat_safety = planner.plan_strategy(event, assistance_level=5)
    assert strat_safety == ResponseStrategy.SAFETY_ALERT

    # 2. Greeting
    strat_greet = planner.plan_strategy(
        event, assistance_level=0, interaction_type=InteractionType.GREETING
    )
    assert strat_greet == ResponseStrategy.GREETING

    # 3. Relationship Cue
    strat_rel = planner.plan_strategy(
        event, assistance_level=0, interaction_type=InteractionType.RELATIONSHIP
    )
    assert strat_rel == ResponseStrategy.RELATIONSHIP_CUE

    # 4. Context Restoration
    strat_attn = planner.plan_strategy(
        event, assistance_level=0, attention_should_interrupt=True
    )
    assert strat_attn == ResponseStrategy.CONTEXT_RESTORATION
