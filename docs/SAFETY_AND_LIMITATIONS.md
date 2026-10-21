# Safety Design and Known Limitations

_Updated 2026-10-21. Describes behaviour as implemented and tested. MEMORA is not a medical
device, has not been clinically evaluated, and must not be relied on for safety,
emergency response, or medication management without human oversight._

## 1. Reply precedence (implemented in `CognitivePipeline.process`)
For every turn, exactly one reply is chosen, in this order:

1. **Urgent concern** in what the person said (`src/clinical/urgent_safety.py`):
   falls, breathing difficulty, chest pain, fainting, bleeding, stroke signs, possible
   overdose, self-harm, explicit help requests. Reply directs the person to their
   configured emergency number / trusted contact / help button and states that MEMORA
   cannot contact anyone. Nothing else may replace or dilute it (battery notices and
   reminders are not appended).
2. **Capability and medical boundaries** (`ConversationalMemory._capability_boundaries`):
   requests to call/message/notify anyone, medication-change questions, diagnosis
   questions — answered plainly ("I can't make calls…", "ask your doctor or pharmacist").
3. **Consent**: if the person has not agreed to storage, nothing is saved and MEMORA says so.
4. **Direct answer from the person's own records** (facts with provenance, corrections,
   object sightings with source and age, schedules, appointments).
5. **Care-policy reply** to what was said (orientation from the clock, validation for
   distress, repetition handling).
6. **Honest fallback** ("I'm not sure I understood…").
7. Without speech: a **scheduled reminder** (throttled) or a **named visitor** announcement.

**Final output check** (`src/clinical/response_guard.py`): every message is checked
immediately before delivery. Claims that MEMORA called, messaged or notified anyone,
dispatched help, that a dose was taken, diagnoses, and medication instructions are
replaced with a safe message and logged. This applies whatever produced the text.

The cognitive-OS `SafetyManager` evaluates an internal proposed action and is
**advisory only** (recorded in the audit trail); it does not gate replies.

## 2. Decisions on behaviour that was previously unspecified
| Topic | Decision | Rationale |
| :--- | :--- | :--- |
| Quiet hours | **Not applied to reminders or urgent guidance.** No other proactive speech exists except visitor announcements and battery notices, which are also not suppressed | Silently dropping or deferring a medication reminder could create a dangerous misunderstanding (e.g. a 22:00 dose). A configurable quiet-hours policy needs clinical/caregiver input and a visible indicator; tracked in MASTER_ROADMAP |
| Reminder frequency | At most once per dose per caregiver-configured interval (default 30 min, minimum 1 min); stops for the day once the person *reports* taking the dose | Avoid nagging while not assuming adherence |
| Dose state | Scheduled → reminded → **reported** taken. MEMORA never records a dose as verified | MEMORA cannot observe medication intake |
| Visitor announcements | Only for identities with a name and relationship; never for unknown faces or the person themself | Avoid misidentification |
| Negated symptoms ("I'm not having chest pain") | Treated as urgent (conservative) | A missed emergency is worse than a gentle prompt; negation handling is not reliable enough to relax this |
| Face recognition | Off unless the person consents (`/consent faces on`) | Biometric data |
| Storage declined | Nothing personal is saved by any path; "I took my pills" is acknowledged but not recorded, and the person is told memory is off; urgent guidance still works | One consent policy (`docs/PRIVACY_AND_CONSENT.md`) |
| Real devices | Used only when `--live-hardware` is given explicitly; no environment variable or profile can enable them | Prevent unexpected recording |
| Requests MEMORA cannot carry out (calls, messages, home devices such as a stove or door lock, booking appointments, reminders by voice) | Say plainly that nothing was done and what to use instead (e.g. "Please check it yourself or ask someone nearby") | Nobody should believe an action happened |
| A face that resembles two stored people | "Not sure who this is": never named, never enrolled as a new person | A wrong name is worse than no name |
| Real camera with no working face-recognition backend | Detect nothing and report `Face Recognition: FAILED (reason)`; never fall back to the simulated recogniser | The simulated recogniser invents a face from every frame |
| Conflicting introduction for a confirmed person | Keep the confirmed name, report a name conflict, store no episode | Prevents attributing one person's words to another |
| Spoken corrections ("Actually, my daughter is Priya") | Replace a single earlier name and say what was changed; with several stored names, ask which one is wrong rather than deleting any | Silent loss or silent duplication of family names would mislead the person |

## 3. Verified (software only)
- Urgent detection: 31 positive/negative phrasings (`tests/test_urgent_safety.py`), simulated
  journeys `urgent_distress`, `medical_boundaries`.
- Output guard: blocked and allowed message sets, and a test that the guard runs on the
  live delivery path (`tests/test_response_guard_and_boundaries.py`).
- Urgent statements take precedence over memory parsing even when they start with a filler or
  correction word (detection runs on the original text before leading words are removed).
- No fabricated people, prescriptions, routines, consent or confidence in real-use
  components (`tests/test_no_invented_context.py`, object-graph sweep).

## 4. Not verified / requires qualified review
- Rule-based English keyword detection; misses phrasings it has not seen and does not
  understand other languages, slurred or garbled speech, or non-verbal distress.
- No real-world, clinical, or usability evaluation with people living with dementia
  or their carers.
- Real speech recognition, text-to-speech, camera, and face recognition are untested;
  ASR errors would change what the safety rules see.
- Emergency numbers are whatever the person or carer entered; MEMORA does not
  validate them against the local emergency system.
- Regulatory status (medical-device rules, health-data and biometric-data law,
  accessibility) has not been assessed by professionals.
