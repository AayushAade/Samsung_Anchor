# Release Gates — Assessment

_2026-10-20, branch `fix/p0-data-isolation-and-safety`; re-assessed in the final handoff audit at
code commit `fafcb78` (CI green on that exact commit; local 756 passed; journeys 20/20). "Pass" means the engineering
evidence listed was produced and reproduced; it is not a claim of clinical, regulatory or
commercial readiness._

| Gate | Verdict | Evidence | What remains |
| :--- | :--- | :--- | :--- |
| **A. Clean installation** | **Pass** | Fresh clone + clean venv at `8ccf2bd` (664 passed, 2 skipped); `git archive` of `ac87a0f` in clean `python:3.13-slim` and `python:3.12-slim` (747 passed, 6 skipped with stated reasons; `--simulate` 20/20; `--check` passes with warnings); GitHub Actions ubuntu/Python 3.11 green | Windows untested |
| **B. Core user journey** | **Pass (text mode)** | 20 simulated journeys through the real `ChatSession` (`app.py --simulate`), incl. consent onboarding, facts, corrections, unknowns, safety, export/delete, restart; Docker CI job checks persistence across container runs | Voice mode not verified |
| **C. Data integrity** | **Pass** | Suite isolated from user data (`tests/conftest.py`; real DB checksum unchanged across all runs since `0b9d3f6`); backup/restore incl. corrupt live DB; additive migrations tested on a copy of the local DB; per-DB face data with integrity check | Local DB already contaminated by pre-isolation test runs — owner decision (PROJECT_STATE §5) |
| **D. Safety behaviour** | **Pass (software)** | Urgent detection (31 cases), output guard on the delivery path, capability/medical boundaries, no fabricated people/drugs (object-graph sweep), journeys `urgent_distress`, `medical_boundaries`; global forbidden-claim check in every journey | Clinical review of phrases and wording; non-English; real ASR errors |
| **E. Simulation honesty** | **Pass with caveats** | Simulated sources labelled (sightings, battery, status table, diagnostics); suite-wide guard proves tests cannot open camera/microphone or make sound (`test_no_physical_devices.py`); simulated data never persisted as real observations; journeys leave the real DB and `data/simulation/` unchanged (checksums/mtimes) | `--simulate` writes metadata lines to the real log (C2-21); chat/`--simulate` stay off real devices only while `MEMORA_PROFILE` is unset (C2-23) |
| **F. Security & privacy** | **Not passed — open defects** | Consent enforced (storage, faces, voice); no silent cloud transcription; 0600 data/log/export/backup files; delete-all covers DB, face data, logs, session state; dashboard XSS escaping, WebSocket origin allow-list, path traversal; LLM output validated; TTS argument hardening; secret scan of full public history clean | **C2-19:** with storage consent declined, a reported dose is still saved. **C2-22:** with the optional faster-whisper extra installed, startup contacts huggingface.co despite "Nothing is sent anywhere". C2-20 policy undocumented. Also: no encryption at rest; no secure erase; consent per database; Gemini API terms review |
| **G. Stability** | **Pass (simulated, ≤ 20 min)** | Soaks in `docs/evidence/` — growth defect found and fixed; post-fix runs flat; thread leak across restarts fixed and checked by the `extended_operation` journey | Multi-hour and real-hardware runs |
| **H. Deployment** | **Pass (core)** | Dockerfile built and run locally and in CI; healthcheck via `--check`; data only in `/data` volume; backup/restore documented and tested | Hardware extras not in image; no image publishing |
| **I. Documentation** | **Pass** | README (verified against the real CLI), PROJECT_STATE, SYSTEM_ARCHITECTURE, CAPABILITY_VERIFICATION_MATRIX (status labels), MASTER_ROADMAP, SAFETY_AND_LIMITATIONS, LICENSING_REVIEW, EXECUTION_LEDGER; historical certification docs marked unsupported | — |
| **J. External readiness** | **Blocked (by design)** | Licensing inventory with primary sources; regulatory questions listed; hardware/cloud items labelled unverified | Repository licence; InsightFace model and AGPL decisions; clinical/usability evaluation; regulatory and privacy review; hardware validation — all require the owner or outside parties |

## Conclusion
The **text-based software is close to, but not yet at,** the bar for a controlled technical pilot.
Before a pilot: fix C2-19 (consent gap for reported doses) and C2-23 (force simulated hardware
when `live_hardware` is false), and either fix C2-22 or deploy the core install only (no
`requirements-hardware.txt`, as in the Docker image). With those addressed, a pilot must still be
supervised, with consenting participants, a person responsible for safety, and non-critical
data. It is **not** ready for unsupervised use by people with memory difficulties, for
real-hardware deployment, or for commercial distribution; Gate J lists what requires the owner
or outside parties.
