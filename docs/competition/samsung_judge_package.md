# MEMORA (Samsung Anchor) — Samsung Solve for Tomorrow Demonstration Package

**Release Candidate**: RC1 (Samsung Solve for Tomorrow Final Evaluation)  
**Target Platform**: Edge AI Cognitive Companion for Dementia Assistance  

---

## 1. Executive Summary & Value Proposition

MEMORA is an edge-first, multimodal cognitive assistance companion engineered specifically for individuals living with Mild Cognitive Impairment (MCI) and Alzheimer's Disease.

Unlike commercial smart assistants (Amazon Alexa, Google Assistant) that require active wake-word recall and rely on cloud LLM processing, MEMORA operates as an **ambient, passive cognitive anchor**. Installed on local edge hardware, MEMORA continuously senses the living environment through camera/microphone HAL adapters, maintains an honest visual memory of misplaced personal items, and governs all interactions using validated dementia care frameworks (**Validation Therapy**, **One-Step Guidance**, **Supportive Silence**).

---

## 2. Key System Innovations & Unique Selling Points (USPs)

1. **Sub-65ms Edge Autonomy**: Runs 100% offline on local hardware with zero external API latency and zero cloud data exfiltration.
2. **Honest Episodic Visual Memory**: Resolves misplaced personal item queries ("Where are my reading glasses?") using spatial room memory without synthesizing or hallucinating locations.
3. **Validation Therapy Engine**: Avoids argumentative corrections ("You already asked that!"); validates patient feelings and provides gentle, reassuring orientation.
4. **Observable Decision Timelines**: Generates structured, step-by-step reasoning traces for every cognitive cycle, streamed live to the Experience Platform Dashboard (`http://localhost:8765`).
5. **Cognitive Safety Rules**: Enforces strict confidence thresholds ($<50\%$ confidence triggers polite refusal), preventing false identity assignments or hallucinated relationships.

---

## 3. Demonstration Guide & Scenarios

### How to Run Demo Mode (One Command)

```bash
# Execute automatic demonstration suite
python demo_mode.py
```

### End-to-End Scenarios Covered

```
[Scenario 1: Family Identity Recognition]
- Recognizes daughter Riya via multi-frame consensus (N=3).
- Output: "Hello Eleanor, your daughter Riya is here." (High Confidence - 95%)

[Scenario 2: Misplaced Item Visual Memory Recall]
- Resolves "Where are my reading glasses?" using spatial memory.
- Output: "Your reading glasses are on the coffee table in the Living Room."

[Scenario 3: Validation Therapy & Repetitive Redirection]
- Patient repeats question: "What time is my appointment?"
- Output: "You are safe here, Eleanor. Your appointment is at 2:00 PM today."

[Scenario 4: Cognitive Safety Rule Enforcement]
- Low confidence face detection (35%).
- Action: Suppresses identity assignment to prevent false identity hallucination.

[Scenario 5: Automated Caregiver Report]
- Automatically generates clinical summary at docs/clinical/clinical_evaluation_report.md.
```

---

## 4. Judge FAQ & Expected Technical Questions

#### Q1: How does MEMORA ensure patient video privacy?
- **Answer**: All visual processing (SCRFD face detection, 128D FAISS embeddings) takes place in local RAM. Video frames are immediately overwritten after feature extraction and are never saved to disk or transmitted over the internet.

#### Q2: What happens if an item is not in MEMORA's visual memory?
- **Answer**: MEMORA applies a strict non-hallucination policy. If an item is not found in spatial memory, MEMORA politely states: *"I haven't seen your reading glasses recently. I will keep an eye out for them in the room."*

#### Q3: Why does MEMORA use Validation Therapy instead of reality orientation?
- **Answer**: Clinical research in geriatric care shows that correcting or arguing with a person living with dementia increases anxiety and catastrophic emotional reactions. Validation Therapy validates the patient's emotional state, building trust and calm.

#### Q4: How is system performance verified?
- **Answer**: MEMORA features a standalone Runtime Validation Framework (`python validate_runtime.py`) that benchmarks FAISS vector search ($0.081\text{ ms}$ avg), memory retrieval ($0.115\text{ ms}$ avg), and continuous RAM usage ($164.6\text{ MB}$).

---

## 5. System Architecture Summary

```
[Camera HAL / Mic HAL]
         │
         ▼
[SensorBus Event Bus]
         │
         ▼
[Bounded Queue (maxsize=10)] ──► Drop-oldest strategy if full
         │
         ▼
[MemoraFaceRecognizer & FAISS Store] ──► Multi-frame consensus (N=3)
         │
         ▼
[Context Fusion Engine] ──► Fuses Identity, Memory, Temporal, Social
         │
         ▼
[Patient State Evaluator] ──► Mode: ORIENTED / SEARCHING / REPETITIVE / ANXIOUS
         │
         ▼
[Care Policy Framework] ──► Policy: Validation Therapy / One-Step Guidance
         │
         ▼
[Explainability & Decision Timeline] ──► Observable reasoning trace
         │
         ▼
[Speaker HAL & Experience WebSockets] ──► Speech output & Web Dashboard (http://localhost:8765)
```
