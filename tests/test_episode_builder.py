from src.cognition.conversation import Conversation
from src.cognition.episode import Episode
from src.cognition.episode_builder import EpisodeBuilder


def test_build_episode_from_conversation():

    builder = EpisodeBuilder()

    conversation = Conversation(
        person="Sid",
        transcript="Worked on Samsung Anchor",
    )

    episode = builder.build(conversation)

    assert isinstance(episode, Episode)
    assert episode.person == "Sid"
    assert episode.summary == "Worked on Samsung Anchor"


def test_summary_is_used_if_present():

    builder = EpisodeBuilder()

    conversation = Conversation(
        person="Sid",
        transcript="Long transcript",
        summary="Worked on memory module",
    )

    episode = builder.build(conversation)

    assert episode.summary == "Worked on memory module"


def test_location_is_preserved():

    builder = EpisodeBuilder()

    conversation = Conversation(
        person="Sid",
        transcript="Meeting",
        location="Living Room",
    )

    episode = builder.build(conversation)

    assert episode.location == "Living Room"


def test_tags_are_preserved():

    builder = EpisodeBuilder()

    conversation = Conversation(
        person="Sid",
        transcript="Samsung discussion",
        tags=["Samsung", "Project"],
    )

    episode = builder.build(conversation)

    assert episode.tags == ["Samsung", "Project"]


def test_commitments_are_preserved():

    builder = EpisodeBuilder()

    conversation = Conversation(
        person="Sid",
        transcript="Let's continue tomorrow",
        commitments=["Continue tomorrow"],
    )

    episode = builder.build(conversation)

    assert episode.commitments == ["Continue tomorrow"]