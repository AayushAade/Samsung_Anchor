# Samsung Anchor — Coordinator Design

**Version:** 1.0

**Status:** Design Specification

---

# Purpose

The Anchor Coordinator is the central orchestration layer of Samsung Anchor.

It is responsible for coordinating communication between independent
subsystems while ensuring that no subsystem becomes tightly coupled to
another.

The Coordinator does **not** perform AI reasoning.

The Coordinator does **not** perform face recognition.

The Coordinator does **not** perform speech recognition.

Instead, it controls the overall application workflow.

---

# Why the Coordinator Exists

Without a Coordinator, subsystems communicate directly.

Example:

Vision
↓

Memory

or

Audio
↓

Reasoning
↓

Memory

As more features are added, this creates strong coupling and makes
the application difficult to maintain.

The Coordinator becomes the single place responsible for application flow.

---

# Responsibilities

The Coordinator is responsible for:

- Receiving events from Vision.
- Receiving events from Audio.
- Invoking the Reasoning subsystem.
- Invoking the Memory subsystem.
- Invoking the Speaker subsystem.
- Managing application state.
- Coordinating future Reminder and Navigation systems.

The Coordinator is NOT responsible for implementing subsystem logic.

---

# What the Coordinator Owns

The Coordinator owns references to:

- MemoraDatabase
- MemoraFaceRecognizer
- MemoraAudioListener
- MemoraContextBinder
- MemoraSpeaker

Future additions:

- Object Tracker
- Reminder Engine
- Navigation Engine
- Conversation Memory

---

# What the Coordinator Does NOT Own

The Coordinator does not contain:

- SQLite logic
- Gemini prompts
- Face recognition algorithms
- Speech recognition algorithms
- Object detection algorithms

These remain inside their respective subsystems.

---

# Application Flow

High-level application flow:

Camera

↓

Vision

↓

Coordinator

↓

Memory

↓

Speaker

For identity learning:

Camera

↓

Unknown Face

↓

Coordinator

↓

Audio Listener

↓

Transcript

↓

Context Binder

↓

Identity Learning Pipeline

↓

Memory

↓

Speaker

---

# Coordinator Responsibilities by Event

## Face Detected

Input

Face embedding

Coordinator actions

- Ask Memory whether identity exists.
- If known:
    - Retrieve identity.
    - Notify Speaker.
- If unknown:
    - Start identity learning workflow.

---

## Transcript Received

Input

Transcript

Coordinator actions

- Send transcript to Context Binder.
- Execute Identity Learning Pipeline.
- Update Memory.
- Trigger confirmation announcements if required.

---

## Object Detected

Future feature.

Coordinator actions

- Update Object Memory.
- Store location history.
- Generate reminders when necessary.

---

## User Question

Future feature.

Example:

"Where are my keys?"

Coordinator actions

- Query Memory.
- Generate response.
- Speak answer.

---

# Coordinator State

The Coordinator should maintain lightweight runtime state.

Examples

Currently visible identities

Currently visible objects

Active reminders

Listening state

Navigation state

Long-term information should always remain inside Memory.

---

# Public Interface

Initial methods

initialize()

start()

shutdown()

process_frame(frame)

process_transcript(face_id, transcript)

handle_identity_confirmation(identity_id)

handle_object_detection(object)

Future methods

handle_question(question)

handle_navigation_request(destination)

handle_reminder(reminder)

---

# Interaction Rules

Subsystems should never call each other directly.

Correct:

Vision

↓

Coordinator

↓

Memory

Incorrect:

Vision

↓

Memory

Correct:

Audio

↓

Coordinator

↓

Reasoning

↓

Memory

Incorrect:

Audio

↓

Memory

---

# Error Handling

Subsystem failures should never crash the application.

Examples

Camera unavailable

↓

Coordinator switches to mock mode.

Microphone unavailable

↓

Coordinator enables manual typing mode.

Gemini unavailable

↓

Coordinator falls back to local heuristics.

Database unavailable

↓

Coordinator reports failure while keeping the application alive.

---

# Future Expansion

The Coordinator is intentionally designed to support:

- Multiple cameras
- Multiple microphones
- Smart glasses
- Wearable hardware
- Cloud synchronization
- Mobile companion application
- Multiple AI models
- Remote caregiver dashboard

No subsystem should require redesign when these features are added.

---

# Design Principles

The Coordinator should remain:

- lightweight
- deterministic
- testable
- modular
- extensible

Business logic belongs inside individual subsystems.

Application flow belongs inside the Coordinator.

---

# Guiding Principle

The Coordinator is the brain of Samsung Anchor.

Subsystems provide capabilities.

The Coordinator decides when and how those capabilities are used.