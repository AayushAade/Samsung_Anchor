"""
Tests for IdentityLearningService.

Detailed integration tests will be added once the
runtime is connected to the service.
"""


def test_identity_learning_service_exists():

    from src.services.identity_learning_service import (
        IdentityLearningService,
    )

    service = IdentityLearningService()

    assert service is not None