# MEMORA — Initial Product Specification (draft)

_Engineering draft, 2026-10-20. Market statements below are hypotheses to test,
not findings. No customer interviews, pricing data or regulatory determinations
exist yet._

## Primary user and buyer
- **Primary user (hypothesis):** an adult living at home with mild memory
  difficulties who can use a conversational assistant independently.
- **Buyer (hypothesis):** often a family caregiver rather than the user; possibly
  care providers later. These may differ and must be validated separately.

## Core problem
Remembering personal facts, recent events and where things were left, without
being corrected or embarrassed, and without exposing private data.

## Minimum viable feature set (what exists today)
- Text conversation that remembers what the person tells it, with source and date.
- Honest recall ("You told me yesterday that…", "I don't have a record of that").
- Corrections that keep history; view, export and delete of all stored data.
- Orientation from the clock; urgent-statement guidance to human help.
- Local-only operation; container deployment.

## Next features (by evidence of need, see MASTER_ROADMAP.md)
Persisted schedules/appointments entered by caregivers; voice I/O; consented
face enrolment for visitor announcement; caregiver view.

## Non-goals
Diagnosis; treatment or medication advice; emergency monitoring or guaranteed
notification; wandering prevention; any claim of clinical validation.

## Privacy expectations
Local storage by default; no audio/video retention; no cloud use for replies;
explicit, documented cloud use only for optional features; user-controlled
export and deletion.

## Success metrics to instrument (pilot)
Recall accuracy on user-confirmed facts; rate of "I don't know" vs wrong answers;
user-reported usefulness; caregiver burden (validated questionnaire chosen with
clinical advisers); zero data-loss incidents.

## Customer discovery plan (to run, not yet run)
1. 10–15 interviews with family caregivers; 5–10 with people with mild memory
   difficulties (with appropriate consent and support).
2. Test hypotheses: (a) caregivers would set up facts/schedules for the user;
   (b) local-only storage is a purchase driver; (c) text/voice on an existing
   device is acceptable vs. dedicated hardware.
3. Supervised usability sessions with the `--chat` build.

## Regulatory questions for professional review
Whether reminders/orientation features fall under medical-device rules in target
markets; health-data privacy obligations (e.g. HIPAA, GDPR special-category data);
biometric data laws for face recognition; accessibility requirements;
consumer-protection limits on marketing claims.

## Differentiation and IP (engineering view)
Most mechanisms are established techniques (rule-based parsing, SQLite, FAISS
nearest-neighbour search). Candidate areas that *may* be distinctive in
combination — provenance-tagged conversational memory with supersession and
"last seen" phrasing; deterministic safety-first reply precedence independent of
any language model — need a prior-art search and qualified patent counsel before
any claim is made. Public disclosure (e.g. a public repository) can affect
patentability; confirm the repository's visibility with counsel. No filing or
legal decision has been made.
