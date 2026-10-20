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

## Next

### P0 — safety, privacy, correctness
1. **Owner decision:** run `--backup` then `--repair` on the local DB (27 faceless identities), or re-enrol.
2. **Decide quiet-hours / throttling policy for proactive speech** (reminders, visitor announcements)
   and enforce it on the actual reply path, or remove the advisory COS SafetyManager from the cycle.
   _Acceptance_: a test proves the chosen policy on spoken output.
4. **Consent records for face enrolment and voice capture** before any real-hardware use.
5. **Licensing:** remove or replace the tracked InsightFace model and AGPL dependencies before any
   commercial build (counsel review); the repository is public.

### P1 — core product
6. **Voice I/O on real hardware** (microphone → ASR → pipeline → TTS), consented and tested on the
   owner's Mac, first with recorded audio fixtures.
7. **Real face enrolment flow** with explicit consent and deletion, verified with consenting subjects.
8. **Person profile persistence** (beyond preferred name): caregiver contacts and emergency number
   used in urgent guidance (currently generic "local emergency number").
9. **Grow the phrasing corpus** from real (consented) usage logs; track coverage over time.

### P2 — operations and quality
10. Versioned schema migrations (additive tables work today via `create_all`; column changes would not).
11. Activate CI (owner approval for GitHub Actions usage).
12. Multi-hour soak and a real-hardware soak once sensors are verified.

### P3 — performance and architecture
13. Lazy-construct or remove the ~20 phase engines that run every cycle without affecting replies.
14. Licence-compatible object detector to replace the contour heuristic.

### P4 — commercial
15. Licensing decisions with counsel — `docs/LICENSING_REVIEW.md`.
16. Customer discovery per `docs/product/PRODUCT_SPEC.md`; regulatory questions for professional review.

## Release stages

| Stage | Entry criteria | Current |
| :--- | :--- | :--- |
| Development | — | **Here** |
| Internal alpha | P0 items 1–4 done; profile/schedules persisted (5); backup/restore (11); owner dogfoods `--chat` daily for 2 weeks with no data loss | not yet |
| Controlled pilot | Real voice I/O verified; consent flows; caregiver configuration; written risk assessment; professional regulatory/privacy review; supervised, consenting participants | not yet |
| Release candidate | Pilot findings resolved; security review; clean-install on target platform; documented rollback | not yet |
| Production | Appropriate regulatory and legal sign-off | not yet |
