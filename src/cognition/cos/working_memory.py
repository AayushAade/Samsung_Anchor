"""
Cognitive Operating System — Working Memory.

Temporary cognitive state storage with automatic TTL-based expiration.
Stores short-lived slots (current conversation topic, active search target,
pending reminder) that should never pollute long-term memory.

Thread-safe. No external dependencies.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from src.cognition.cos.models import WorkingMemorySlot


class WorkingMemory:
    """
    Slot-based temporary cognitive storage with configurable TTL expiration.

    Each slot has an independent time-to-live. Stale slots are garbage-collected
    at the start of every kernel reasoning cycle via ``expire_stale()``.
    """

    MAX_SLOTS = 20
    DEFAULT_TTL = 300.0  # 5 minutes

    def __init__(self) -> None:
        self._slots: dict[str, WorkingMemorySlot] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """
        Store or overwrite a working memory slot.

        Parameters
        ----------
        key : str
            Slot identifier (e.g., ``"current_conversation"``, ``"active_search"``).
        value : Any
            The cognitive state to hold temporarily.
        ttl_seconds : float, optional
            Time-to-live in seconds. Defaults to ``DEFAULT_TTL``.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.DEFAULT_TTL
        with self._lock:
            self._slots[key] = WorkingMemorySlot(
                key=key, value=value, stored_at=time.time(), ttl_seconds=ttl,
            )
            self._enforce_capacity()

    def recall(self, key: str) -> Any | None:
        """
        Recall a working memory slot value. Returns ``None`` if absent or expired.
        """
        with self._lock:
            slot = self._slots.get(key)
            if slot is None or slot.is_expired:
                return None
            return slot.value

    def update_interaction(
        self,
        user_message: str,
        assistant_response: str = "",
        room: str | None = None,
        people: list[str] | None = None,
        objects: list[str] | None = None,
        activity: str | None = None,
        reminders: list[str] | None = None,
        goals: list[str] | None = None,
        topic: str | None = None,
    ) -> None:
        """
        Continuously update working memory slots for every interaction turn.
        """
        self.store("previous_user_message", user_message)
        if assistant_response:
            self.store("previous_assistant_response", assistant_response)
        if room is not None:
            self.store("current_room", room)
        if people is not None:
            self.store("current_people", people)
        if objects is not None:
            self.store("current_detected_objects", objects)
        if activity is not None:
            self.store("current_activity", activity)
        if reminders is not None:
            self.store("active_reminders", reminders)
        if goals is not None:
            self.store("active_goals", goals)
        if topic is not None:
            self.store("current_topic", topic)

        # Detect search intent or object targets in user message to update active_search_target
        lower_msg = user_message.lower()
        search_keywords = ["where is", "where are", "looking for", "find my", "lost my", "need my", "where did i put"]
        for kw in search_keywords:
            if kw in lower_msg:
                # Extract target object substring
                target = lower_msg.split(kw)[-1].strip(" ?.!'")
                # Clean leading articles
                for article in ["my ", "the ", "a ", "an "]:
                    if target.startswith(article):
                        target = target[len(article):]
                if target:
                    self.store("active_search_target", target)
                    self.store("current_topic", f"Searching for {target}")
                break

    def resolve_reference(self, query: str) -> dict[str, Any]:
        """
        Perform conversational reference (anaphora) resolution using active working memory slots.

        Resolves relative pronouns ("them", "it", "they", "that", "him", "her", "there")
        to concrete entities stored in working memory without artificial hardcoding.
        """
        words = query.split()
        lower_query = query.lower()
        
        pronoun_map = {
            "them": None,
            "it": None,
            "they": None,
            "that": None,
            "him": None,
            "her": None,
            "there": None,
        }

        # Check if any target pronoun exists in query
        detected_pronoun = None
        for p in pronoun_map:
            if f" {p} " in f" {lower_query} " or lower_query.endswith(f" {p}?") or lower_query.endswith(f" {p}."):
                detected_pronoun = p
                break

        if not detected_pronoun:
            return {
                "original_query": query,
                "resolved_query": query,
                "has_reference": False,
                "resolved_referent": None,
            }

        # Identify candidate referent from working memory slots
        referent = None
        
        # 1. Active Search Target (highest priority for "them", "it", "that")
        search_target = self.recall("active_search_target")
        if search_target and detected_pronoun in ["them", "it", "they", "that"]:
            referent = search_target

        # 2. Detected objects / current topic
        if not referent and detected_pronoun in ["them", "it", "they", "that"]:
            objs = self.recall("current_detected_objects")
            if objs and len(objs) > 0:
                referent = objs[0] if isinstance(objs[0], str) else str(objs[0])
            elif self.recall("current_topic"):
                referent = self.recall("current_topic")

        # 3. People for "him", "her", "them"
        if not referent and detected_pronoun in ["him", "her", "them"]:
            people = self.recall("current_people")
            if people and len(people) > 0:
                referent = people[0]

        # 4. Room for "there"
        if not referent and detected_pronoun == "there":
            referent = self.recall("current_room")

        if not referent:
            return {
                "original_query": query,
                "resolved_query": query,
                "has_reference": True,
                "resolved_referent": None,
            }

        # Construct resolved query
        # Replace the pronoun with referent or "the <referent>"
        referent_phrase = f"the {referent}" if not referent.lower().startswith("the ") else referent
        resolved_words = []
        for w in words:
            clean_w = w.strip("?.!,'\"").lower()
            if clean_w == detected_pronoun:
                punctuation = w[len(clean_w):] if len(w) > len(clean_w) else ""
                resolved_words.append(f"{referent_phrase}{punctuation}")
            else:
                resolved_words.append(w)

        resolved_query = " ".join(resolved_words)

        return {
            "original_query": query,
            "resolved_query": resolved_query,
            "has_reference": True,
            "resolved_referent": referent,
            "pronoun": detected_pronoun,
        }

    def expire_stale(self) -> int:
        """
        Remove all expired slots. Returns the number of slots evicted.
        Called at the start of every kernel reasoning cycle.
        """
        with self._lock:
            before = len(self._slots)
            self._slots = {
                k: v for k, v in self._slots.items() if not v.is_expired
            }
            return before - len(self._slots)

    def snapshot(self) -> dict[str, Any]:
        """
        Return a serialisable snapshot of all active (non-expired) slots.
        """
        with self._lock:
            return {
                "slot_count": len(self._slots),
                "slots": {
                    k: v.to_dict()
                    for k, v in self._slots.items()
                    if not v.is_expired
                },
            }

    def clear(self) -> None:
        """Remove all slots."""
        with self._lock:
            self._slots.clear()

    @property
    def active_slot_count(self) -> int:
        with self._lock:
            return sum(1 for v in self._slots.values() if not v.is_expired)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _enforce_capacity(self) -> None:
        """Drop oldest slots if capacity exceeded."""
        while len(self._slots) > self.MAX_SLOTS:
            oldest_key = min(self._slots, key=lambda k: self._slots[k].stored_at)
            del self._slots[oldest_key]

