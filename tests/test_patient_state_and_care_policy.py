from src.clinical.patient_state import PatientStateEvaluator, PatientStateMode
from src.clinical.care_policy import CarePolicyFramework, CarePrinciple
from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline


def test_patient_state_evaluator_modes():
    evaluator = PatientStateEvaluator()

    # 1. Emergency Override
    s1 = evaluator.evaluate(emergency_active=True)
    assert s1.mode == PatientStateMode.EMERGENCY
    assert s1.confidence == 1.0

    # 2. Missed Medication
    s2 = evaluator.evaluate(missed_medications=["Donepezil"])
    assert s2.mode == PatientStateMode.AWAITING_REMINDER

    # 3. Repetitive Queries
    evaluator.evaluate(user_speech="What time is my appointment?")
    s3 = evaluator.evaluate(user_speech="What time is my appointment?")
    assert s3.mode == PatientStateMode.REPETITIVE

    # 4. Searching for Item
    evaluator.reset()
    s4 = evaluator.evaluate(user_speech="Where are my glasses?")
    assert s4.mode == PatientStateMode.SEARCHING

    # 5. Anxiety
    evaluator.reset()
    s5 = evaluator.evaluate(user_speech="I am worried and frightened")
    assert s5.mode == PatientStateMode.ANXIOUS


def test_care_policy_framework_dementia_principles():
    framework = CarePolicyFramework()
    evaluator = PatientStateEvaluator()

    # Validation Therapy for Anxiety
    anxious_state = evaluator.evaluate(user_speech="I am scared")
    decision1 = framework.evaluate_policy(anxious_state, patient_name="Eleanor", location="Living Room")
    assert decision1.principle == CarePrinciple.VALIDATION_THERAPY
    assert "safe here at home" in decision1.message_override

    # Repetitive Query Redirection
    evaluator.evaluate(user_speech="When is lunch?")
    rep_state = evaluator.evaluate(user_speech="When is lunch?")
    decision2 = framework.evaluate_policy(rep_state, patient_name="Eleanor")
    assert decision2.principle == CarePrinciple.REPETITIVE_REDIRECTION
    assert "everything is taken care of" in decision2.message_override

    # Emergency Escalation
    emerg_state = evaluator.evaluate(emergency_active=True)
    decision3 = framework.evaluate_policy(emerg_state)
    assert decision3.principle == CarePrinciple.EMERGENCY_ESCALATION
    assert decision3.action_type == "ESCALATE"


def test_cognitive_pipeline_integration_with_care_policy():
    db = MemoraDatabase("sqlite:///:memory:")
    pipeline = CognitivePipeline(db)

    # Ingest query into cognitive cycle
    rec_result = {
        "face_id": "1",
        "name": "Eleanor",
        "relationship": "Patient",
        "user_speech": "Where are my keys?",
    }

    actions = pipeline.process(rec_result)
    assert hasattr(pipeline, "current_patient_state")
    assert pipeline.current_patient_state.mode in [
        PatientStateMode.AWAITING_REMINDER,
        PatientStateMode.SEARCHING,
        PatientStateMode.ORIENTED,
    ]

    pipeline.shutdown()
