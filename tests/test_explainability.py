from src.clinical.explainability import ExplainabilityEngine


def test_explainability_engine_explanations():
    engine = ExplainabilityEngine()
    exp = engine.explain_decision(
        presence_allowed=True,
        assistance_level=2,
        strategy="Gentle Hint",
        reason="Routine memory cue",
    )

    assert "Presence Policy permitted cue" in exp.reason
    assert "Level 2" in exp.reason
    assert exp.dignity_check_passed is True
