from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from src.cognition.memory_models import RelevantMemory

class ContextFreshness(Enum):
    REALTIME = "REALTIME"
    RECENT = "RECENT"
    STALE = "STALE"
    ARCHIVED = "ARCHIVED"

@dataclass
class ConflictTrace:
    domain: str
    description: str
    resolved_confidence: float

@dataclass
class IdentityContext:
    face_id: str
    name: Optional[str]
    relationship: Optional[str]
    confidence: float
    is_known: bool

@dataclass
class MemoryContext:
    memories: List[RelevantMemory]
    confidence: float

@dataclass
class TemporalContext:
    current_time: datetime
    time_of_day: str # e.g. "Morning", "Afternoon"
    day_of_week: str
    confidence: float

@dataclass(frozen=True)
class CognitiveContext:
    """
    The unified understanding of the user's present context.
    Produced by the ContextFusionEngine.
    """
    timestamp: datetime
    
    # Core Domains
    identity: Optional[IdentityContext]
    memory: Optional[MemoryContext]
    temporal: Optional[TemporalContext]
    continuity: Optional[Any] = None
    social: Optional[Any] = None
    assistance: Optional[Any] = None
    
    # Future Extension Points (Left as None for now)
    spatial: Optional[Any] = None
    medical: Optional[Any] = None
    
    # Fusion Metadata
    conflict_traces: List[ConflictTrace] = field(default_factory=list)
    provider_latencies: Dict[str, float] = field(default_factory=dict)
    dropped_providers: List[str] = field(default_factory=list)
