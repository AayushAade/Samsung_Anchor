from typing import Protocol
from src.cognition.memory_models import RelevantMemory
from src.cognition.attention.attention_models import CognitiveState
from src.cognition.memory_taxonomy import MemoryImportance

class AttentionScorer(Protocol):
    """
    Protocol for modular cognitive heuristics.
    Returns a score indicating how much attention a specific memory 
    deserves in the current cognitive state.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        ...

class BaseImportanceScorer:
    """
    Evaluates the absolute baseline importance of the memory.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        # Scale: LOW=10, NORMAL=20, HIGH=30, CRITICAL=40
        return memory.importance.value * 10.0

class RecencyScorer:
    """
    Evaluates how recently a memory was formed or reinforced.
    Recent memories generally demand slightly more attention, 
    but very old memories decay in attention relevance unless highly important.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        if not memory.timestamp:
            return 0.0
            
        delta = state.current_time - memory.timestamp
        days_old = delta.total_seconds() / 86400.0
        
        # Max +15 for brand new memories. Rapidly decays.
        return max(0, 15.0 / (days_old + 1))

class MedicalUrgencyScorer:
    """
    Heavily boosts attention for medical or emergency-related memories.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        # We can look for keywords or rely on Importance=CRITICAL
        score = 0.0
        if memory.importance == MemoryImportance.CRITICAL:
            score += 40.0
        if "medicine" in memory.summary.lower() or "pill" in memory.summary.lower():
            score += 20.0
        return score

class CommitmentScorer:
    """
    Boosts attention for active, unresolved commitments or promises.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        if memory.commitments and len(memory.commitments) > 0:
            return 25.0
        return 0.0

class AdaptiveAttentionScorer:
    """
    Adjusts attention based on the memory's historical usefulness and frequency.
    Learns from user feedback over time.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        usefulness = getattr(memory, 'historical_usefulness', 0.5)
        return (usefulness - 0.5) * 30.0


class NoveltyScorer:
    """
    Evaluates the novelty of a memory or event.
    First-time or rare events demand heightened attention.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        access_count = getattr(memory, 'access_count', 1)
        if access_count <= 1:
            return 20.0
        elif access_count <= 3:
            return 10.0
        return 0.0


class ConfidenceScorer:
    """
    Scales attention by the upstream perceptual and retrieval confidence.
    High-confidence memories have higher attention priority.
    """
    def score(self, memory: RelevantMemory, state: CognitiveState) -> float:
        confidence = getattr(memory, 'confidence', 1.0)
        return confidence * 15.0

