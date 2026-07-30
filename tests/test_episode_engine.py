from src.cognition.conversation import Conversation
from src.cognition.episode_builder import EpisodeBuilder
from src.cognition.episode_engine import EpisodeEngine
from src.cognition.episode_repository import EpisodeRepository


def test_remember_creates_episode():

    repo = EpisodeRepository()

    engine = EpisodeEngine(
        builder=EpisodeBuilder(),
        repository=repo,
    )

    conversation = Conversation(
        person="Sid",
        transcript="Worked on Samsung Anchor",
    )

    episode = engine.remember(conversation)

    assert repo.count() == 1
    assert repo.latest_episode() == episode
    assert episode.person == "Sid"
    assert episode.summary == "Worked on Samsung Anchor"