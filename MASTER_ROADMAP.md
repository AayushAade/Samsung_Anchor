# MEMORA — Master Roadmap

_Prioritised from verified findings (see PROJECT_STATE.md and
CAPABILITY_VERIFICATION_MATRIX.md). Updated 2026-10-21._

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

## Done in the remediation mission (2026-10-21)
| Pri | Item | Commit |
| :--- | :--- | :--- |
| P1 | One consent policy for every write, incl. commands, reported doses and logs (C2-19, C2-20) | `fa5213f` |
| P1 | Real devices only via `--live-hardware` (C2-23); `--vision-standalone` included | `0ecfd68`, `5583a4c` |
| P1 | Explicit network policy, socket-level tests (C2-22) | `977d8ff` |
| P2 | `--simulate` isolated from the normal environment (C2-21); test temp cleanup | `03c7c29` |
| P2 | Backup-manifest path validation; owner-only export temp file | `5583a4c` |
| P1 | Corrections and statements starting with "Actually", "No,", "Well," | `93c5563` |
| P2 | End-to-end CLI journey test; CI on Python 3.11/3.12/3.13 | `09cf8ac` |

## Done in the final completion mission (2026-10-21)
| Pri | Item | Commit |
| :--- | :--- | :--- |
| P1 | Identity evidence needs consent at the storage layer; conflicting names never attributed to a confirmed person | `8296de8` |
| P2 | `/export` contains every stored personal record | `64085cb` |
| P1 | `--check` read-only (it had migrated a pre-existing database) | `5f753f6` |
| P2 | Text mode never loads PyAV; macOS duplicate `libavdevice` risk characterised (R-09) | `8d4ba7d` |
| P2 | Dashboard loads nothing from the internet | `b978dfd` |
| P0 | Live recogniser no longer fabricates faces from real frames; reports when no backend works | `b00922f` |
| P2 | Clean development database tool | `99ddcff` |
| P1 | "Where I put things", no place-as-name facts, honest action boundaries, "remind me who…" | `2990621` |

## Next

### Owner decisions (blocking)
1. Local DB: restore the pre-work backup or start a fresh database (test contamination).
2. Licensing: repository licence (options in `docs/LICENSING_REVIEW.md` §6); stop
   redistributing `assets/models/scrfd_500m_bnkps.onnx`? InsightFace/YOLO commercial licences or
   replacements; record `assets/images/banner.png` provenance.
3. Authorise real-hardware testing (camera, microphone, speaker) on a named machine; include
   ledger R-09 (PyAV/OpenCV duplicate `libavdevice` on macOS).
4. Authorise a Gemini test key (or decide to drop cloud name extraction).
5. Merge PR #1 into `main` after review.

### P1 — product
5a. A working, licence-cleared face-recognition backend (D3), then hardware testing
    (`docs/HARDWARE_TEST_CHECKLIST.md`).
5b. Supervised technical pilot of the text product (`docs/PILOT_CHECKLIST.md`) once authorised.
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
