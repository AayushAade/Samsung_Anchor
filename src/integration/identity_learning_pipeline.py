"""
Identity Learning Pipeline

This module orchestrates the identity learning workflow between the
Audio, Reasoning, and Memory subsystems.

Responsibilities
----------------
- Accept a transcript associated with a detected face.
- Use the Context Binder to extract structured identity information.
- Record the extracted evidence in the Memory subsystem.
- Return a structured result describing the outcome.

This module deliberately contains NO database logic,
NO speech recognition logic, and NO AI prompting logic.
Those responsibilities remain inside their respective
subsystems.
"""

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from src.memory.database import MemoraDatabase
    from src.reasoning.context_binder import MemoraContextBinder


def process_identity_learning(
    face_id: str,
    transcript: str,
    database: "MemoraDatabase",
    binder: "MemoraContextBinder",
) -> Dict[str, Any]:
    """
    Coordinate transcript parsing and identity learning.

    Parameters
    ----------
    face_id : str
        Identity currently assigned by the Vision subsystem.

    transcript : str
        Raw transcript obtained from the Audio subsystem.

    database : MemoraDatabase
        Memory subsystem instance.

    binder : MemoraContextBinder
        Reasoning subsystem instance.

    Returns
    -------
    dict
        Structured result describing the learning outcome.
    """

    # ---------------------------------------------------------
    # Basic input validation
    # ---------------------------------------------------------

    if not face_id:
        return {
            "success": False,
            "reason": "Missing face_id",
        }

    if not transcript or not transcript.strip():
        return {
            "success": False,
            "reason": "Empty transcript",
        }

    # ---------------------------------------------------------
    # Parse transcript into structured information
    # ---------------------------------------------------------

    parsed = binder.parse_transcript(transcript)

    if not isinstance(parsed, dict):
        return {
            "success": False,
            "reason": "Invalid parser response",
        }

    name = parsed.get("name")
    relationship = parsed.get("relationship")

    if not name:
        return {
            "success": False,
            "reason": "No identity information extracted",
        }

    # ---------------------------------------------------------
    # Record evidence in the Memory subsystem
    # ---------------------------------------------------------

    result = database.add_evidence(
        identity_id=face_id,
        name=name,
        relationship=relationship,
        raw_transcript=transcript,
    )

    if result is None:
        return {
            "success": False,
            "reason": "Failed to record evidence",
        }

    # ---------------------------------------------------------
    # Success
    # ---------------------------------------------------------

    return {
        "success": True,
        "identity_id": face_id,
        "name": result["name"],
        "relationship": result["relationship"],
        "confidence": result["confidence"],
        "is_confirmed": result["is_confirmed"],
    }