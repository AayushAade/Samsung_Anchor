"""
Helpers for tests that exercise storage. Saving what a person says requires
their consent (ConsentFeature.CONVERSATION_STORAGE); tests that check memory
behaviour grant it explicitly, exactly as a person would during onboarding.
"""

from __future__ import annotations

from src.clinical.clinical_models import ConsentFeature


def allow_memory(pipeline):
    pipeline.consent_mgr.update_consent(ConsentFeature.CONVERSATION_STORAGE, True)
    return pipeline


def allow_faces(pipeline):
    pipeline.consent_mgr.update_consent(ConsentFeature.FACE_RECOGNITION, True)
    return pipeline
