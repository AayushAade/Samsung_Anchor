"""
MEMORA Central Cognitive I/O Engine.

Public façade coordinating InputGateway, IOValidator, IORouter, and OutputGateway.
Serves as the exclusive boundary authority through which all inputs enter and outputs leave.
"""

from __future__ import annotations

import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Tuple

from src.io.input_gateway import InputGateway
from src.io.io_models import IOMessage, IOSnapshot, InputType, OutputType, RoutingDecision
from src.io.io_router import IORouter
from src.io.io_validator import IOValidator
from src.io.output_gateway import OutputGateway


class IOEngine:
    """
    Unified public façade for Cognitive Input/Output Framework.
    """

    def __init__(self) -> None:
        self.input_gateway = InputGateway()
        self.output_gateway = OutputGateway()
        self.router = IORouter()
        self.validator = IOValidator()
        self._rejected_count = 0
        self._lock = threading.Lock()

    def receive(
        self,
        source: str,
        input_type: InputType,
        payload_reference: str,
        destination: str = "CognitivePipeline",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[IOMessage, RoutingDecision]:
        # 1. Ingress normalization
        msg = self.input_gateway.receive_input(
            source=source,
            input_type=input_type,
            payload_reference=payload_reference,
            destination=destination,
            metadata=metadata,
            session_id=session_id,
        )

        # 2. Validation
        valid, val_reason = self.validator.validate_message(msg)
        if not valid:
            with self._lock:
                self._rejected_count += 1
            decision = RoutingDecision(
                destination=destination,
                accepted=False,
                reason=f"Validation failed: {val_reason}",
                validation_status="REJECTED",
            )
            return msg, decision

        # 3. Deterministic routing
        decision = self.router.route(msg)
        return msg, decision

    def route(self, message: IOMessage) -> RoutingDecision:
        valid, val_reason = self.validator.validate_message(message)
        if not valid:
            with self._lock:
                self._rejected_count += 1
            return RoutingDecision(
                destination=message.destination,
                accepted=False,
                reason=f"Validation failed: {val_reason}",
                validation_status="REJECTED",
            )
        return self.router.route(message)

    def send(
        self,
        destination: str,
        output_type: OutputType,
        payload_reference: str,
        source: str = "CognitivePipeline",
        metadata: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> IOMessage:
        # 1. Egress normalization
        msg = self.output_gateway.prepare_output(
            destination=destination,
            output_type=output_type,
            payload_reference=payload_reference,
            source=source,
            metadata=metadata,
            session_id=session_id,
        )

        # 2. Validate outbound envelope
        valid, _ = self.validator.validate_message(msg)
        if valid:
            self.router.route(msg)
        else:
            with self._lock:
                self._rejected_count += 1

        return msg

    def validate(self, message: IOMessage) -> Tuple[bool, str]:
        return self.validator.validate_message(message)

    def compute_checksum(self) -> str:
        with self._lock:
            rec = [m.message_id for m in self.input_gateway.get_received_messages()]
            sent = [m.message_id for m in self.output_gateway.get_sent_messages()]
            raw = json.dumps({"rec": sorted(rec), "sent": sorted(sent)}).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

    def snapshot(self) -> IOSnapshot:
        with self._lock:
            rec_count = len(self.input_gateway.get_received_messages())
            sent_count = len(self.output_gateway.get_sent_messages())
            routed_count = len(self.router.get_routed_decisions())
            rejected = self._rejected_count
            chk = self.compute_checksum()

            return IOSnapshot(
                received_messages_count=rec_count,
                sent_messages_count=sent_count,
                routed_messages_count=routed_count,
                rejected_messages_count=rejected,
                checksum=chk,
            )

    def reset(self) -> None:
        with self._lock:
            self.input_gateway.clear()
            self.output_gateway.clear()
            self.router.clear()
            self.validator.clear()
            self._rejected_count = 0
