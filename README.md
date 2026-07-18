# Samsung Anchor

Samsung Anchor is an AI-powered **Computational Cognitive Architecture** and Artificial External Hippocampus designed to assist people with memory impairments (such as Alzheimer's and Dementia patients) by continually understanding context, remembering experiences, and inferring goals.

This repository serves as a research-grade cognitive system, focusing on modularity, explainability, and cognitive realism.

## Current Project Status: Phase 3 Release Candidate

Samsung Anchor has successfully completed three major phases of cognitive development:

1. **Phase 1: Memory Intelligence**
   - **Persistent Episodic Memory**: Stores and retrieves real-life experiences naturally using an event-driven runtime and SQLAlchemy + FAISS persistence layer.
   - **Semantic Knowledge Graph**: Translates episodic experiences into semantic facts and preferences.
   - **Memory Consolidation & Intelligent Forgetting**: Learns from experiences, solidifies important facts, and gracefully decays unused memories over time.
   - **Identity Learning**: Recognizes known individuals, registers anonymous faces, and learns their identities through natural interaction.

2. **Phase 2: Context Intelligence**
   - **Context Fusion Engine**: Concurrent execution of context providers (Identity, Memory, Temporal) with strict timeouts to build unified situational awareness (`CognitiveContext`). Gracefully degrades if providers fail.
   - **Cognitive Attention Engine**: Acts as the Executive Function. Scores memories dynamically based on current context (time, location, identity) to decide whether to interrupt the user or remain in "Cognitive Silence."

3. **Phase 3: Goal Intelligence**
   - **Intent & Goal Reasoning Framework**: Shifts the system from asking "What do I know?" to "What is the user trying to accomplish?"
   - **Goal Inference Engine**: Evaluates evidence from memory, time, and identity to hypothesize user goals (e.g., "Medication Routine", "Morning Routine").
   - **Goal Lifecycle**: Goals evolve from HYPOTHESIZED to ACTIVE, accumulating confidence via Bayesian-like evidence aggregation, and eventually decaying to ABANDONED or COMPLETED.

## System Architecture

The core runtime orchestration is managed by the `AnchorCoordinator` communicating asynchronously over an Event Bus. The true intelligence occurs in the `CognitivePipeline`:

```text
Perception → Context Fusion → Goal Inference → Executive Function → LLM (Context Restoration) → Interaction
```

### Key Modules

- **`ContextFusionEngine`**: Gathers multi-domain context efficiently.
- **`GoalInferenceEngine`**: Reasons over context to predict user intent.
- **`CognitiveAttentionEngine`**: Scores memories against context/goals and decides if an interaction is warranted.
- **`ContextRestorationEngine`**: Formulates a structured prompt (combining context, goals, and memories) for the LLM to generate a natural, context-aware cue.
- **`MemoryEngine` & `CognitiveMemoryManager`**: Manages the flow of raw experiences into the episodic database, consolidates them into the semantic graph, and handles decay/forgetting.

## Observability

The `CognitiveInspector` provides deep tracing of the cognitive loop, rendering latencies, dropped providers, goal hypotheses (with supporting/contradicting evidence), and executive attention decisions in a readable developer trace.

## Getting Started

Start the live end-to-end cognitive loop (requires webcam):
```bash
source .venv/bin/activate
python live_demo.py
```

Run independent cognitive scenario tests:
```bash
python scratch/test_goal_reasoning.py
python scratch/test_context_fusion.py
python scratch/test_e2e_cognitive_loop.py
```

Run the complete test suite:
```bash
python -m pytest tests/ -v
```
