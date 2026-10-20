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

## Next

### P0 — safety, privacy, correctness
1. **Restrict on-disk permissions** for the DB and embedding files (0600) and document at-rest
   encryption options. _Acceptance_: new DB/embedding files created 0600; test proves it.
2. **Decide what to do with the 27 orphaned identities** in the local DB (owner decision:
   delete or re-enrol). Provide a `--repair` command that lists and, on confirmation,
   deletes identities without embeddings. _Acceptance_: tested on a copy; never automatic.
3. **Make `SafetyManager` either gate output or be removed from the reply path claims.**
   _Acceptance_: a test shows an unsafe proposed action is blocked, or docs/audit no
   longer imply gating.
4. **Stop storing MEMORA's own replies as "memories"** (`MemoryEncoder` in the pipeline) or
   tag them as system output so they can never be recalled as user facts.

### P1 — core product
5. **Persist the person's profile, medication schedules and appointments**, with chat
   commands to add/list/remove them (caregiver-entered data labelled as such).
6. **Reported vs verified medication state**: handle "I took it" as a *reported* action;
   never mark as verified.
7. **Voice I/O on real hardware** (microphone → ASR → pipeline → TTS) behind explicit
   consent, tested on the owner's Mac with recorded fixtures first.
8. **Real face enrolment flow** (explicit consent, delete on request) and verification with
   consenting test subjects.
9. Remove or relabel the remaining "Eleanor" placeholder in `experience/dashboard/app.js`
   and audit the dashboard for synthetic values.

### P2 — operations and quality
10. Schema migrations (Alembic or a minimal versioned migrator) with tests on DB copies.
11. Backup/restore command (`--backup`, `--restore`) with integrity verification.
12. Lint/format/type-check configuration (ruff, mypy on new modules) and a secret scan;
    activate CI once the owner approves Actions usage.
13. Replace stdout prints in the pipeline with logging; quiet by default.
14. Long-duration stability run (≥ 1 h simulated, with recorded memory/thread/latency).

### P3 — performance and architecture
15. Lazy-construct the ~20 phase engines that do not influence replies, or remove them
    from the per-cycle path; measure startup and per-turn latency before/after.
16. Real object detection with a licence-compatible model (YOLO/Ultralytics is AGPL-3.0).

### P4 — commercial
17. Licensing decisions (repository licence, AGPL and model terms) with counsel —
    see `docs/LICENSING_REVIEW.md`.
18. Product specification, customer-discovery plan, and regulatory questions list —
    see `docs/product/PRODUCT_SPEC.md`.

## Release stages

| Stage | Entry criteria | Current |
| :--- | :--- | :--- |
| Development | — | **Here** |
| Internal alpha | P0 items 1–4 done; profile/schedules persisted (5); backup/restore (11); owner dogfoods `--chat` daily for 2 weeks with no data loss | not yet |
| Controlled pilot | Real voice I/O verified; consent flows; caregiver configuration; written risk assessment; professional regulatory/privacy review; supervised, consenting participants | not yet |
| Release candidate | Pilot findings resolved; security review; clean-install on target platform; documented rollback | not yet |
| Production | Appropriate regulatory and legal sign-off | not yet |
