"""
MEMORA Uncertainty & Evidence Management — Evidence Accumulator.

Replaces static floating-point scores with multi-observation temporal evidence pools.
Supports temporal decay, multi-source accumulation, conflict detection, and
human-explainable evidence summaries.
"""

from __future__ import annotations

import math
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from src.trust.models import (
    EvidencePoolSummary,
    EvidenceRecord,
    EvidenceType,
)


class EvidenceAccumulator:
    """
    Manages multi-observation evidence pools with temporal decay over time.

    Supports tracking evidence for:
      - Face / Identity recognitions
      - Household object sightings
      - Patient state observations
      - Goal hypotheses
    """

    DEFAULT_DECAY_HALFLIFE_SECONDS = 600.0  # 10 minutes

    def __init__(self, decay_halflife_seconds: float = 600.0) -> None:
        self.decay_halflife_seconds = decay_halflife_seconds
        # Entity Key -> List of EvidenceRecords
        self._pools: Dict[str, List[EvidenceRecord]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_evidence(
        self,
        entity_key: str,
        evidence_type: EvidenceType,
        source: str,
        key: str,
        value: str,
        weight: float = 0.25,
        confidence: float = 0.85,
    ) -> str:
        """
        Record a new piece of evidence for an entity key.

        Parameters
        ----------
        entity_key : str
            Unique key identifying the entity (e.g. ``"identity:Sarah"``, ``"object:Glasses"``).
        evidence_type : EvidenceType
            Domain of evidence.
        source : str
            Subsystem producing the evidence (e.g. ``"FaceRecognizer"``).
        key : str
            Evidence signal descriptor (e.g. ``"face_matched"``).
        value : str
            Observed value string.
        weight : float
            Contribution weight (positive = supporting, negative = contradicting).
        confidence : float
            Observation confidence score.

        Returns
        -------
        str
            Generated evidence ID.
        """
        rec_id = f"ev-{uuid.uuid4().hex[:8]}"
        record = EvidenceRecord(
            evidence_id=rec_id,
            evidence_type=evidence_type,
            source=source,
            key=key,
            value=value,
            weight=weight,
            confidence=confidence,
            timestamp=time.time(),
        )

        with self._lock:
            if entity_key not in self._pools:
                self._pools[entity_key] = []
            self._pools[entity_key].append(record)

            # Cap max pool size per entity to 50 records
            if len(self._pools[entity_key]) > 50:
                self._pools[entity_key] = self._pools[entity_key][-50:]

        return rec_id

    def get_summary(self, entity_key: str) -> EvidencePoolSummary:
        """
        Compute decaying accumulated evidence summary for an entity.
        """
        with self._lock:
            records = list(self._pools.get(entity_key, []))

        if not records:
            return EvidencePoolSummary(
                entity_key=entity_key,
                supporting_count=0,
                contradicting_count=0,
                accumulated_confidence=0.0,
                net_weight=0.0,
                is_conflicted=False,
                explanation="No evidence observations recorded.",
            )

        now = time.time()
        decay_constant = math.log(2) / self.decay_halflife_seconds

        supporting_count = 0
        contradicting_count = 0
        total_pos_weight = 0.0
        total_neg_weight = 0.0

        for r in records:
            age = max(0.0, now - r.timestamp)
            decay = math.exp(-decay_constant * age)
            effective_weight = r.weight * r.confidence * decay

            if r.weight >= 0:
                supporting_count += 1
                total_pos_weight += effective_weight
            else:
                contradicting_count += 1
                total_neg_weight += abs(effective_weight)

        net_weight = total_pos_weight - total_neg_weight
        denominator = total_pos_weight + total_neg_weight + 1.0
        acc_confidence = min(0.98, max(0.0, total_pos_weight / denominator))

        is_conflicted = total_neg_weight > (0.30 * total_pos_weight) and total_neg_weight > 0.15

        if is_conflicted:
            explanation = (
                f"Conflicting evidence detected for '{entity_key}': "
                f"{supporting_count} supporting (w={total_pos_weight:.2f}), "
                f"{contradicting_count} contradicting (w={total_neg_weight:.2f})."
            )
        elif supporting_count > 0:
            explanation = (
                f"Strong evidence accumulation for '{entity_key}': "
                f"{supporting_count} observations, accumulated confidence {acc_confidence:.0%}."
            )
        else:
            explanation = f"Insufficient evidence recorded for '{entity_key}'."

        return EvidencePoolSummary(
            entity_key=entity_key,
            supporting_count=supporting_count,
            contradicting_count=contradicting_count,
            accumulated_confidence=acc_confidence,
            net_weight=net_weight,
            is_conflicted=is_conflicted,
            explanation=explanation,
        )

    def explain_evidence(self, entity_key: str) -> str:
        """Return a detailed human-readable breakdown of evidence for clinical audit."""
        summary = self.get_summary(entity_key)
        return summary.explanation

    def purge_decayed_evidence(self, max_age_seconds: float = 3600.0) -> int:
        """
        Remove evidence records older than `max_age_seconds`.
        Returns total records purged.
        """
        now = time.time()
        purged = 0
        with self._lock:
            for k in list(self._pools.keys()):
                before = len(self._pools[k])
                self._pools[k] = [r for r in self._pools[k] if (now - r.timestamp) <= max_age_seconds]
                purged += before - len(self._pools[k])
                if not self._pools[k]:
                    del self._pools[k]
        return purged

    def reset(self) -> None:
        with self._lock:
            self._pools.clear()
