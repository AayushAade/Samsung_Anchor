from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AssistanceLevel(Enum):
    """
    Graduated Assistance Levels:
    Level 0: Observe (Silent observation)
    Level 1: Encourage (Subtle encouragement, positive validation)
    Level 2: Gentle Hint (Short indirect cue)
    Level 3: Context Restoration (Full situation & relationship context)
    Level 4: Direct Assistance (Step-by-step guidance)
    Level 5: Safety Intervention (Urgent direct safety instruction)
    """

    LEVEL_0 = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5

    @property
    def label(self) -> str:
        labels = {
            0: "Level 0: Observe",
            1: "Level 1: Encourage",
            2: "Level 2: Gentle Hint",
            3: "Level 3: Context Restoration",
            4: "Level 4: Direct Assistance",
            5: "Level 5: Safety Intervention",
        }
        return labels.get(self.value, "Level 0: Observe")

    @property
    def name_simple(self) -> str:
        names = {
            0: "Observe",
            1: "Encourage",
            2: "Gentle Hint",
            3: "Context Restoration",
            4: "Direct Assistance",
            5: "Safety Intervention",
        }
        return names.get(self.value, "Observe")


@dataclass
class AssistanceContext:
    """
    Context output by the AssistanceContextProvider for the current cognitive cycle.
    """

    level: AssistanceLevel
    level_code: int
    level_label: str
    rationale: str
    escalation_triggered: bool = False
    support_history_count: int = 0
    confidence: float = 1.0
