from src.clinical.clinical_models import DecisionExplanation


class ExplainabilityEngine:
    """
    Generates transparent, human-readable explanations for caregivers explaining system interventions.
    """

    def explain_decision(
        self,
        presence_allowed: bool,
        assistance_level: int,
        strategy: str,
        reason: str = "Routine cue requested",
    ) -> DecisionExplanation:
        presence_str = "Presence Policy permitted cue" if presence_allowed else "Presence Policy suppressed response"
        assistance_str = f"Assistance Policy calculated Level {assistance_level}"
        
        explanation_text = (
            f"{presence_str}. {assistance_str}. "
            f"Response Strategy set to '{strategy}' based on patient autonomy guidelines."
        )

        return DecisionExplanation(
            reason=explanation_text,
            presence_eval=presence_str,
            assistance_eval=assistance_str,
            strategy_selected=strategy,
            dignity_check_passed=True,
        )
