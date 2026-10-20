from unittest.mock import patch

from devices.speaker import SpeakerDevice
from src.interaction.actions import (
    InteractionAction,
    InteractionActionType,
)


@patch("devices.speaker.subprocess.Popen")  # never run the real `say` (no sound in tests)
@patch("builtins.print")
def test_execute_speak(mock_print, mock_popen):

    speaker = SpeakerDevice()

    action = InteractionAction(
        type=InteractionActionType.SPEAK,
        message="Hello Samsung Anchor",
    )

    speaker.execute(action)

    mock_print.assert_called_once_with(
        "Hello Samsung Anchor"
    )
    mock_popen.assert_called_once_with(["say", "Hello Samsung Anchor"])
