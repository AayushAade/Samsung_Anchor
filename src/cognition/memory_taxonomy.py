from enum import Enum

class MemoryCategory(Enum):
    """
    Extensible taxonomy for Semantic Memory (Knowledge Graph nodes).
    """
    RELATIONSHIP = "relationship"
    PREFERENCE = "preference"
    ROUTINE = "routine"
    MEDICAL = "medical"
    COMMITMENT = "commitment"
    SPATIAL = "spatial"
    OBJECT = "object"
    CONVERSATION = "conversation"
    HABIT = "habit"
    FACT = "fact"

class MemoryImportance(Enum):
    """
    Importance levels matching the previous schema but for semantic knowledge.
    """
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
