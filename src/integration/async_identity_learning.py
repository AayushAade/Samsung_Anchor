"""
Async Identity Learning

Runs identity learning in a background thread so the
camera feed remains smooth while audio is processed.
"""

from __future__ import annotations

import threading

from src.integration.identity_learning_pipeline import (
    process_identity_learning,
)


def start_identity_learning(
    *,
    face_id: str,
    listener,
    binder,
    database,
    speaker=None,
    on_finished=None,
) -> threading.Thread:
    """
    Launch identity learning in a background thread.

    Parameters
    ----------
    face_id
        Anonymous identity currently assigned by Vision.

    listener
        MemoraAudioListener.

    binder
        MemoraContextBinder.

    database
        MemoraDatabase.

    speaker
        Optional SpeakerDevice.

    on_finished
        Optional callback:
            callback(face_id, result)
    """

    def worker():

        try:

            print("\n🧠 I don't think we've met before.")
            print("Please introduce yourself.\n")

            transcript = listener.listen_and_transcribe()

            if not transcript:

                result = {
                    "success": False,
                    "reason": "No transcript captured",
                }

            else:

                result = process_identity_learning(
                    face_id=face_id,
                    transcript=transcript,
                    database=database,
                    binder=binder,
                )

                if (
                    speaker is not None
                    and result.get("success")
                    and result.get("is_confirmed")
                ):
                    print(
                        f"\n✅ Learned identity: {result['name']}"
                    )

            if on_finished is not None:
                on_finished(face_id, result)

        except Exception as exc:

            print(
                f"\n[Identity Learning Error] {exc}"
            )

            if on_finished is not None:
                on_finished(
                    face_id,
                    {
                        "success": False,
                        "reason": str(exc),
                    },
                )

    thread = threading.Thread(
        target=worker,
        daemon=True,
    )

    thread.start()

    return thread