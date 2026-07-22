# Memora Architecture Guide

## Overview
Memora is built around a decoupled, modular cognitive architecture divided into seven core domains:

1. **Hardware Runtime Layer (`src/runtime/`)**: Hardware Abstraction Layer (HAL) isolating physical hardware adapters behind a thread-safe `SensorBus`.
2. **Edge Perception Layer (`src/perception/`)**: Real-time vision, room location, household object detection, activity recognition, audio classification, and multimodal fusion.
3. **Cognitive Core (`src/cognition/`, `src/memory/`)**: Context fusion, memory retrieval repository, identity context, and goal inference engines.
4. **Graduated Assistance Policy Engine (`src/cognition/assistance_policy_engine.py`)**: Evaluates patient confidence and provides graduated support levels (Observe, Encourage, Hint, Context Restore, Direct Guide, Safety Override).
5. **Human-Centered Conversation Engine (`src/conversation/`)**: Turn manager, dialogue state machine, active speaker inference, and supportive silence strategies.
6. **Clinical Ecosystem Layer (`src/clinical/`)**: Structured patient profiles, multi-caregiver access, medication schedules, privacy consent, audit logging, explainability rationales, and emergency safety overrides.
7. **Deployment & Observability (`deployment/`)**: Profile-driven configuration, multi-component health checker, metrics telemetry, structured JSON logging, Docker containerization, and Experience Platform UI.
