# Release Gates — Assessment

_2026-10-20, branch `fix/p0-data-isolation-and-safety`. "Pass" means the engineering
evidence listed was produced and reproduced; it is not a claim of clinical, regulatory or
commercial readiness._

| Gate | Verdict | Evidence | What remains |
| :--- | :--- | :--- | :--- |
| **A. Clean installation** | **Pass** | Fresh clone + clean venv at `8ccf2bd` (664 passed, 2 skipped); `git archive` of `ac87a0f` in clean `python:3.13-slim` and `python:3.12-slim` (747 passed, 6 skipped with stated reasons; `--simulate` 20/20; `--check` passes with warnings); GitHub Actions ubuntu/Python 3.11 green | Windows untested |
| **B. Core user journey** | **Pass (text mode)** | 20 simulated journeys through the real `ChatSession` (`app.py --simulate`), incl. consent onboarding, facts, corrections, unknowns, safety, export/delete, restart; Docker CI job checks persistence across container runs | Voice mode not verified |
| **C. Data integrity** | **Pass** | Suite isolated from user data (`tests/conftest.py`; real DB checksum unchanged across all runs since `0b9d3f6`); backup/restore incl. corrupt live DB; additive migrations tested on a copy of the local DB; per-DB face data with integrity check | Local DB already contaminated by pre-isolation test runs — owner decision (PROJECT_STATE §5) |
| **D. Safety behaviour** | **Pass (software)** | Urgent detection (31 cases), output guard on the delivery path, capability/medical boundaries, no fabricated people/drugs (object-graph sweep), journeys `urgent_distress`, `medical_boundaries`; global forbidden-claim check in every journey | Clinical review of phrases and wording; non-English; real ASR errors |
| **E. Simulation honesty** | **Pass** | Simulated sources labelled (sightings, battery, status table, diagnostics); suite-wide guard proves tests cannot open camera/microphone or make sound (`test_no_physical_devices.py`); simulated data never persisted as real observations | — |
| **F. Security & privacy** | **Pass with open items** | Consent enforced (storage, faces, voice); no silent cloud transcription; 0600 data/log/export/backup files; delete-all covers DB, face data, logs, session state; dashboard XSS escaping, WebSocket origin allow-list, path traversal; LLM output validated; TTS argument hardening; secret scan of full public history clean | No encryption at rest; no secure erase; consent is per database; Gemini API terms review |
| **G. Stability** | **Pass (simulated, ≤ 20 min)** | Soaks in `docs/evidence/` — growth defect found and fixed; post-fix runs flat; thread leak across restarts fixed and checked by the `extended_operation` journey | Multi-hour and real-hardware runs |
| **H. Deployment** | **Pass (core)** | Dockerfile built and run locally and in CI; healthcheck via `--check`; data only in `/data` volume; backup/restore documented and tested | Hardware extras not in image; no image publishing |
| **I. Documentation** | **Pass** | README (verified against the real CLI), PROJECT_STATE, SYSTEM_ARCHITECTURE, CAPABILITY_VERIFICATION_MATRIX (status labels), MASTER_ROADMAP, SAFETY_AND_LIMITATIONS, LICENSING_REVIEW, EXECUTION_LEDGER; historical certification docs marked unsupported | — |
| **J. External readiness** | **Blocked (by design)** | Licensing inventory with primary sources; regulatory questions listed; hardware/cloud items labelled unverified | Repository licence; InsightFace model and AGPL decisions; clinical/usability evaluation; regulatory and privacy review; hardware validation — all require the owner or outside parties |

## Conclusion
The **text-based software** meets the engineering gates for a **controlled technical pilot**
(supervised, consenting participants, synthetic or non-critical data, a human responsible
for safety). It is **not** ready for unsupervised use by people with memory difficulties,
for real-hardware deployment, or for commercial distribution. Gate J and the open items above
define what must happen first.
