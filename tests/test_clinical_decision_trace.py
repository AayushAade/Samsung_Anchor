from src.clinical.patient_state import PatientStateEvaluator, PatientStateMode
from src.clinical.care_policy import CarePolicyFramework
from src.clinical.decision_trace import ClinicalDecisionTraceLogger
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


def test_clinical_decision_trace_logger_fields():
    evaluator = PatientStateEvaluator()
    framework = CarePolicyFramework()
    logger = ClinicalDecisionTraceLogger()

    # Evaluate PatientState & CarePolicy
    p_state = evaluator.evaluate(user_speech="Where are my glasses?")
    care_decision = framework.evaluate_policy(p_state, current_message="Glasses are on table.", patient_name="Eleanor")

    trace = logger.record_trace(
        patient_state=p_state,
        cognitive_context=None,
        goal_hypotheses=None,
        care_decision=care_decision,
        interaction_strategy="CONTEXT_RESTORATION",
        speech_produced=True,
        memory_written=True,
        final_response="Glasses are on table.",
    )

    assert trace.patient_state == "Searching for Item"
    assert "Locate missing personal item" in trace.patient_state_evidence
    assert "identity" in trace.providers_consulted
    assert "memory" in trace.providers_consulted
    assert "Validation Therapy" in trace.care_policies_evaluated
    assert trace.selected_care_policy == "One-Step Guidance"
    assert trace.speech_produced is True
    assert trace.memory_written is True
    assert trace.final_response == "Glasses are on table."
    assert "patient_state_confidence" in trace.confidence_scores


def test_cognitive_pipeline_records_clinical_decision_trace():
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    rec_result = {
        "face_id": "1",
        "name": "Eleanor",
        "relationship": "Patient",
        "user_speech": "What time is my doctor appointment?",
    }

    pipeline.process(rec_result)

    assert hasattr(pipeline, "latest_clinical_trace")
    trace = pipeline.latest_clinical_trace

    assert trace is not None
    assert isinstance(trace.providers_consulted, list)
    assert len(trace.providers_consulted) >= 5
    assert isinstance(trace.memory_retrieval_summary, str)
    assert trace.selected_care_policy is not None

    pipeline.shutdown()
