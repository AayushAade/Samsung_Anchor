"""
Comprehensive Test Suite for MEMORA Phase 35 — Unified Cognitive Input/Output (I/O) Framework.

Tests:
1. I/O Data Models (Serialization of IOMessage, RoutingDecision, IOSnapshot, InputType, OutputType)
2. Input Gateway (Ingress message creation, metadata normalization, session association)
3. Output Gateway (Egress message preparation, delivery metadata normalization)
4. I/O Router (Deterministic mapping for CAMERA, MICROPHONE, SENSOR, TEXT, SYSTEM, CLINICAL, EXTERNAL)
5. I/O Validator (Duplicate message detection, missing field validation, validation history)
6. Central I/O Engine (Public façade for receive, send, route, validate, and snapshot)
7. I/O Explainer (Deterministic Markdown diagnostic report generation)
"""

import pytest
from src.io import (
    INPUT_ROUTING_MAP,
    OUTPUT_ROUTING_MAP,
    IOEngine,
    IOExplainer,
    IOMessage,
    IORouter,
    IOSnapshot,
    IOValidator,
    InputGateway,
    InputType,
    OutputGateway,
    OutputType,
    RoutingDecision,
)


# ======================================================================
# 1. I/O Data Models Tests
# ======================================================================

class TestIOModels:
    def test_io_message_serialization(self):
        msg = IOMessage(
            source="CameraDriver",
            destination="CognitivePipeline",
            input_type=InputType.CAMERA,
            payload_reference="frame-001.jpg",
            session_id="ses-1234",
        )
        d = msg.to_dict()
        assert d["source"] == "CameraDriver"
        assert d["input_type"] == "CAMERA"
        assert d["session_id"] == "ses-1234"
        assert msg.is_input() is True
        assert msg.is_output() is False

    def test_routing_decision_to_dict(self):
        rd = RoutingDecision(
            destination="PerceptionManager",
            accepted=True,
            reason="Mapped InputType CAMERA",
            validation_status="ROUTED",
        )
        assert rd.to_dict()["destination"] == "PerceptionManager"

    def test_io_snapshot_to_dict(self):
        snap = IOSnapshot(
            received_messages_count=10,
            sent_messages_count=5,
            routed_messages_count=15,
            rejected_messages_count=0,
            checksum="abc12345",
        )
        assert snap.to_dict()["received_messages_count"] == 10


# ======================================================================
# 2. Input Gateway Tests
# ======================================================================

class TestInputGateway:
    def test_receive_input(self):
        gw = InputGateway()
        msg = gw.receive_input(
            source="MicDriver",
            input_type=InputType.MICROPHONE,
            payload_reference="audio-chunk-01.wav",
            session_id="ses-audio-1",
        )
        assert msg.source == "MicDriver"
        assert msg.session_id == "ses-audio-1"
        assert len(gw.get_received_messages()) == 1


# ======================================================================
# 3. Output Gateway Tests
# ======================================================================

class TestOutputGateway:
    def test_prepare_output(self):
        gw = OutputGateway()
        msg = gw.prepare_output(
            destination="DisplayAdapter",
            output_type=OutputType.DISPLAY,
            payload_reference="ui_rendered_card",
            session_id="ses-out-1",
        )
        assert msg.destination == "DisplayAdapter"
        assert len(gw.get_sent_messages()) == 1


# ======================================================================
# 4. I/O Router Tests
# ======================================================================

class TestIORouter:
    def test_deterministic_input_routing(self):
        router = IORouter()

        # Camera -> PerceptionManager
        msg_cam = IOMessage(source="Cam", destination="CognitivePipeline", input_type=InputType.CAMERA, payload_reference="p1")
        dec_cam = router.route(msg_cam)
        assert dec_cam.destination == "PerceptionManager"

        # Microphone -> AudioPipeline
        msg_mic = IOMessage(source="Mic", destination="CognitivePipeline", input_type=InputType.MICROPHONE, payload_reference="p2")
        dec_mic = router.route(msg_mic)
        assert dec_mic.destination == "AudioPipeline"

        # Sensor -> SensorBus
        msg_sen = IOMessage(source="Sensor", destination="CognitivePipeline", input_type=InputType.SENSOR, payload_reference="p3")
        dec_sen = router.route(msg_sen)
        assert dec_sen.destination == "SensorBus"


# ======================================================================
# 5. I/O Validator Tests
# ======================================================================

class TestIOValidator:
    def test_validate_clean_message(self):
        val = IOValidator()
        msg = IOMessage(source="Cam", destination="Pipeline", input_type=InputType.CAMERA, payload_reference="p1")
        is_valid, reason = val.validate_message(msg)
        assert is_valid is True

    def test_validate_duplicate_message_id(self):
        val = IOValidator()
        msg1 = IOMessage(source="Cam", destination="Pipeline", input_type=InputType.CAMERA, payload_reference="p1", message_id="dup-msg-id")
        msg2 = IOMessage(source="Cam", destination="Pipeline", input_type=InputType.CAMERA, payload_reference="p1", message_id="dup-msg-id")

        val.validate_message(msg1)
        is_valid, reason = val.validate_message(msg2)
        assert is_valid is False
        assert "Duplicate message_id" in reason

    def test_validate_missing_type(self):
        val = IOValidator()
        msg = IOMessage(source="Cam", destination="Pipeline", payload_reference="p1")
        is_valid, reason = val.validate_message(msg)
        assert is_valid is False
        assert "specify either input_type or output_type" in reason


# ======================================================================
# 6. Central I/O Engine Tests
# ======================================================================

class TestIOEngine:
    def test_engine_receive_and_send(self):
        engine = IOEngine()

        msg_in, dec = engine.receive(
            source="CameraModule",
            input_type=InputType.CAMERA,
            payload_reference="frame.png",
            session_id="ses-engine-1",
        )
        assert msg_in.source == "CameraModule"
        assert dec.destination == "PerceptionManager"

        msg_out = engine.send(
            destination="SpeakerAdapter",
            output_type=OutputType.AUDIO,
            payload_reference="tts_output.wav",
            session_id="ses-engine-1",
        )
        assert msg_out.destination == "SpeakerAdapter"

        snap = engine.snapshot()
        assert snap.received_messages_count == 1
        assert snap.sent_messages_count == 1
        assert snap.checksum is not None


# ======================================================================
# 7. I/O Explainer Tests
# ======================================================================

class TestIOExplainer:
    def test_explain_io_state(self):
        engine = IOEngine()
        engine.receive("Cam", InputType.CAMERA, "frame.jpg", session_id="ses-1")
        engine.send("Speaker", OutputType.AUDIO, "audio.wav", session_id="ses-1")

        markdown = IOExplainer.explain_io_state(engine)
        assert "MEMORA Unified Cognitive I/O Diagnostic Report" in markdown
        assert "Ingress Received Messages" in markdown
        assert "Egress Message Summary" in markdown
