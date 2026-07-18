"""
Episode Repository

Stores and retrieves episodic memories.

This repository is intentionally in-memory for now.
A persistent implementation (SQLite) can replace it later
without changing the public API.
"""

from __future__ import annotations

from typing import List, Optional

from src.cognition.episode import Episode


class EpisodeRepository:
    """
    Repository for episodic memories.
    """

    def __init__(self) -> None:
        self._episodes: List[Episode] = []

    # ---------------------------------------------------------
    # Storage
    # ---------------------------------------------------------

    def add_episode(self, episode: Episode) -> None:
        """
        Store an episode.
        """
        self._episodes.append(episode)

    # ---------------------------------------------------------
    # Retrieval
    # ---------------------------------------------------------

    def latest_episode(self) -> Optional[Episode]:
        """
        Return the most recently stored episode.
        """

        if not self._episodes:
            return None

        return self._episodes[-1]

    def episodes_for_person(self, person: str) -> List[Episode]:
        """
        Return every episode involving a person.
        """

        return [
            episode
            for episode in self._episodes
            if episode.person.lower() == person.lower()
        ]

    # ---------------------------------------------------------
    # Maintenance
    # ---------------------------------------------------------

    def clear(self) -> None:
        """
        Remove every stored episode.
        """

        self._episodes.clear()

    def count(self) -> int:
        """
        Return the number of stored episodes.
        """

        return len(self._episodes)