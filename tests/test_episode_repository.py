from src.cognition.episode import Episode
from src.cognition.episode_repository import EpisodeRepository


def test_repository_starts_empty():
    repo = EpisodeRepository()

    assert repo.count() == 0
    assert repo.latest_episode() is None


def test_add_episode():
    repo = EpisodeRepository()

    episode = Episode(
        person="Sid",
        summary="Worked on Samsung Anchor",
    )

    repo.add_episode(episode)

    assert repo.count() == 1


def test_latest_episode():
    repo = EpisodeRepository()

    first = Episode(
        person="Sid",
        summary="Episode One",
    )

    second = Episode(
        person="Sid",
        summary="Episode Two",
    )

    repo.add_episode(first)
    repo.add_episode(second)

    assert repo.latest_episode() == second


def test_person_lookup():
    repo = EpisodeRepository()

    repo.add_episode(
        Episode(
            person="Sid",
            summary="Samsung meeting",
        )
    )

    repo.add_episode(
        Episode(
            person="Rahul",
            summary="Family dinner",
        )
    )

    repo.add_episode(
        Episode(
            person="Sid",
            summary="Memory module",
        )
    )

    episodes = repo.episodes_for_person("Sid")

    assert len(episodes) == 2


def test_clear_repository():
    repo = EpisodeRepository()

    repo.add_episode(
        Episode(
            person="Sid",
            summary="Something",
        )
    )

    repo.clear()

    assert repo.count() == 0
    assert repo.latest_episode() is None