from unittest.mock import patch

from devices.speaker import SpeakerDevice
from src.interaction.actions import (
    InteractionAction,
    InteractionActionType,
)


@patch("builtins.print")
def test_execute_speak(mock_print):

    speaker = SpeakerDevice()

    action = InteractionAction(
        type=InteractionActionType.SPEAK,
        message="Hello Samsung Anchor",
    )

    speaker.execute(action)

    mock_print.assert_called_once_with(
        "Hello Samsung Anchor"
    )