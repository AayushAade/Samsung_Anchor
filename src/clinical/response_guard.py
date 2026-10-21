"""
Deterministic checks applied to every message immediately before delivery.

This is the last safety layer on the live output path: whatever produced a
reply (rules, templates, recall of stored text, or a language model), the
message is checked here before it is spoken or displayed.

It blocks claims MEMORA cannot truthfully make:
- that it contacted, called, messaged, alerted or notified anyone, or
  dispatched help (no such integration exists);
- that a medication dose was taken (only the person's *report* can be
  recorded, never a verification);
- diagnoses or medication instructions.

Quoting the person back ("you told me ...") is allowed; the guard only checks
MEMORA's own assertions, so recalled user statements are exempted by marker.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_CONTACT_CLAIM = re.compile(
    r"\b(i(?:'ve| have)?|we(?:'ve| have)?|memora (?:has )?)\s*(?:just |already )?"
    r"(called|phoned|rang|texted|messaged|emailed|alerted|notified|contacted|informed|dispatched|sent (?:a |an )?"
    r"(?:message|alert|notification|text))\b"
    r"|\b(caregiver|carer|clinical team|doctor|family|emergency services|ambulance|help)\b[^.]{0,40}"
    r"\b(has been|have been|was|were|is being|are being)\s+(notified|alerted|called|contacted|informed|dispatched)\b"
    r"|\bhelp is on (?:the|its) way\b",
    re.IGNORECASE,
)
_DOSE_CLAIM = re.compile(
    r"\byou(?:'ve| have)?\s+(?:already |just )?(?:took|taken|had)\s+(?:your |the )?"
    r"(?:dose|pills?|medicines?|medications?|tablets?)\b"
    r"|\b(?:dose|medication|medicine|pills?)\b[^.]{0,30}\b(?:has|have) been taken\b"
    r"|\b(?:dose|medication|medicine)\b[^.]{0,20}\bconfirmed\b",
    re.IGNORECASE,
)
_CLINICAL_CLAIM = re.compile(
    r"\byou (?:have|probably have|might have|are suffering from)\s+(?:a |an )?"
    r"(dementia|alzheimer'?s|a stroke|a heart attack|an infection|covid|cancer|diabetes|pneumonia)\b"
    r"|\byou should (?:take|stop taking|double|skip|increase|reduce)\b[^.]{0,40}\b(dose|pills?|medicines?|medications?|tablets?)\b",
    re.IGNORECASE,
)

# Text inside these markers is the person's own words being quoted back.
_QUOTED = re.compile(r"(you told me[^.;]*|you said \"[^\"]*\")", re.IGNORECASE)


@dataclass(frozen=True)
class GuardResult:
    message: str
    blocked: bool
    reason: Optional[str] = None


SAFE_REPLACEMENT = ("I'm sorry, I can't say that reliably. I can't contact anyone, I can't confirm "
                    "whether medicine was taken, and I can't give medical advice. If you need help, "
                    "please call your local emergency number or someone you trust.")


def check_outgoing(message: Optional[str]) -> GuardResult:
    """Return the message unchanged if it is safe, otherwise a safe replacement."""
    if not message:
        return GuardResult(message or "", False)
    own_words = _QUOTED.sub(" ", message)
    for name, pattern in (("contact_claim", _CONTACT_CLAIM), ("dose_claim", _DOSE_CLAIM),
                          ("clinical_claim", _CLINICAL_CLAIM)):
        if pattern.search(own_words):
            logger.warning("Response guard blocked an outgoing message (%s).", name)
            return GuardResult(SAFE_REPLACEMENT, True, name)
    return GuardResult(message, False)
