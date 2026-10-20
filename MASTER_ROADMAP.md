# MEMORA — Master Roadmap

_Prioritised from verified findings (see PROJECT_STATE.md and
CAPABILITY_VERIFICATION_MATRIX.md). Updated 2026-10-20._

## Done in this cycle (all on `fix/p0-data-isolation-and-safety`)

| Pri | Item | Commit |
| :--- | :--- | :--- |
| P0 | Shared face index across all databases; `clear()` deleted real embeddings; tests wrote to the user DB | `0b9d3f6` |
| P0 | Urgent statements ("I fell", "I can't breathe") echoed back; false "caregiver notified"; seeded prescriptions and object sightings shown to every user | `00160c6` |
| P0 | Wrong recall, names learned from "I am tired", unrelated facts returned, fabricated answers | `cdddbba` |
| P0 | 9 runtime modules never committed (clean clone could not import); double speech; fabricated telemetry/status | `90eab3c` |
| P1 | Usable product loop: `--chat` with view/correct/export/delete | `85134ff` |
| P2 | Reproducible install, working container, `--check`, Gemini hardening | `823a85e` |
| P0 | Scenario validator never compared results; unspoken reminders; visitors never announced | `9f47497` |
| P0 | 0600 data files; `--repair`; own replies no longer stored as memories ("temp" id overwrite) | `e2b97f3` |
| P0 | Audit `final_action` now records what was actually done (COS SafetyManager is advisory) | `f4d1cd9` |
| P1 | Persisted schedules/appointments with entry commands; reported-dose tracking | `f4d1cd9` |
| P2 | Backup/restore | `4695a8a` |
| P2 | Bug-focused static analysis gate; 3 runtime NameErrors fixed | `34ef886` |
| P1 | Dashboard fictional defaults / false "meds confirmed" | `ecec514` |
| P0 | Own turns stored under "Eleanor" and counted as visits | `87f6e94` |
| P0 | Unbounded face-track memory growth (found by soak) | `609d2e8` |
| P2 | Logging with rotation; quiet console; soak harness and evidence | `4bd4968`, `17ba5ed` |
| P0 | Dashboard XSS sinks; invented routine/escalation/consent/confidence | `1abc9ed` |
| P0 | Fictional people/prescriptions in knowledge, LTM, caregivers, relationships, personalisation | `839ea7b` |
| P1 | Emergency number + trusted contact in urgent guidance | `44f385f` |
| P1 | Phrasing coverage measured (corpus 40/40) | `cdd1465` |

## Done in cycle 2 (2026-10-20)
| Pri | Item | Commit |
| :--- | :--- | :--- |
| P0 | Response guard on the delivery path; honest call/medication/diagnosis answers | `3354043` |
| P1 | Conflicting relations surfaced, corrections, retraction, pronouns, names | `cef558c`, `bbca359` |
| P0 | Consent enforced (storage, faces) with chat onboarding | `e5fbee3` |
| P2 | Actionable storage errors; delete-all covers logs and session state | `1bc192a` |
| P2 | Versioned additive migrations; sighting source stated | `8313383` |
| P1 | Simulation: clock, battery, sensor failures, 20 journeys; restore-on-corrupt and thread-leak fixes | `0666d05` |
| P2 | CI (GitHub Actions) — green | `8c671ec` |
| P0 | Tests could drive real devices/sound; honest speaker fallback | `466be66` |
| P0 | Silent cloud transcription of microphone audio; voice consent; SpeechRecognition optional | `592ddab` |
| P2 | Core verified on Python 3.12/3.13 | `ac87a0f` |
| P0 | Dashboard WebSocket cross-site hijacking | `e4dc941` |

## Next (re-ranked after the final handoff audit at `fafcb78`)

### Fix before any pilot (found in the audit; small, not yet done)
0a. C2-19 — with storage consent declined, do not save reported doses; say memory is off.
0b. C2-23 — force simulated hardware whenever `live_hardware` is false (chat, `--simulate`).
0c. C2-22 — load speech recognition lazily and offline by default; disclose any model download
    (or deploy the core install only).
0d. C2-21 — `--simulate` logs into its own temporary directory.
0e. C2-20 — decide and document whether explicit commands may save without storage consent.

### Owner decisions (blocking)
1. Local DB: restore the pre-work backup or start a fresh database (test contamination).
2. Licensing: repository licence; stop redistributing `assets/models/scrfd_500m_bnkps.onnx`?
   InsightFace/YOLO commercial licences or replacements.
3. Authorise real-hardware testing (camera, microphone, speaker) on a named machine.
4. Authorise a Gemini test key (or decide to drop cloud name extraction).
5. Merge PR #1 into `main` after review.

### P1 — product
6. Voice mode end to end (local ASR, e.g. faster-whisper, instead of cloud) with consent,
   verified first with recorded audio fixtures, then on hardware.
7. Caregiver-mediated setup (schedules, contacts, consent on behalf of the person) — needs
   product and legal input.
8. Grow the phrasing corpus from consented pilot usage; measure false answers explicitly.

### P2 — reliability and security
9. Encryption at rest for the database and face data (OS keychain-backed key).
10. Multi-hour soak; real-hardware soak once sensors are verified.
11. Remove or lazy-load the phase engines that do not affect replies (simplicity, startup).

### P3 — commercialisation
12. Third-party notices generated at release; customer-discovery plan execution
    (`docs/product/PRODUCT_SPEC.md`); professional regulatory review.

## Release stages

| Stage | Entry criteria | Current |
| :--- | :--- | :--- |
| Development | — | Passed |
| Internal alpha / controlled technical pilot (text mode) | Engineering gates A–I (see `docs/RELEASE_GATES.md`); owner dogfoods `--chat` for 2 weeks with no data loss | **Engineering gates met; dogfooding not started** |
| Controlled pilot | Real voice I/O verified; consent flows; caregiver configuration; written risk assessment; professional regulatory/privacy review; supervised, consenting participants | not yet |
| Release candidate | Pilot findings resolved; security review; clean-install on target platform; documented rollback | not yet |
| Production | Appropriate regulatory and legal sign-off | not yet |
