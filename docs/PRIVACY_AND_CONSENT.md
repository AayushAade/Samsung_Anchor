# Privacy and Consent Policy (as implemented)

_Enforced in code and verified by `tests/test_consent_policy.py`, `tests/test_consent_enforcement.py`,
`tests/test_cloud_asr_and_voice_consent.py` and the `consent_declined` journey._

## Consents
| Consent (`/consent …`) | Feature | Required for |
| :--- | :--- | :--- |
| `memory` | `CONVERSATION_STORAGE` | **Every** persistent personal record: facts and preferences, preferred name, conversation episodes, object sightings, medication schedules, appointments, reported doses, emergency number, trusted contact, identity-learning transcripts and derived knowledge |
| `faces` | `FACE_RECOGNITION` | Matching or enrolling faces (biometric embeddings, identity records, name evidence). Identity learning also needs `memory` |
| `voice` | `VOICE_RECORDING` | Recording from a real microphone. Online transcription additionally needs `MEMORA_ALLOW_CLOUD_ASR=1` |

Consent is never assumed: every feature starts off. First use of `--chat` asks for `memory`
before anything else.

## What is stored regardless of consent
Only non-personal records needed to operate: the consent decisions themselves
(`consent:<feature>` with timestamp), `schema_version`, and system defaults
(`current_room`, `next_anon_index`). Nothing the person says.

## What happens without `memory` consent
- Statements are not stored; MEMORA says memory is turned off instead of "I'll remember".
- `/add-medication`, `/add-appointment`, `/set-emergency-number`, `/set-trusted-contact` are refused
  with an explanation (medication reminders therefore cannot be set up).
- "I took my pills" is acknowledged but **not** recorded.
- Urgent guidance still works (with the generic "local emergency number").
- Diagnostic output that could echo what was said is discarded instead of logged.
- The storage layer (`CareStore`, `ConversationalMemory._save_fact`) raises
  `ConsentRequiredError` if any code path bypasses these checks.

## Revoking consent
`/consent memory off` stops new writes immediately. Records already saved are kept until the
person removes them (`/forget N`, `/remove-medication N`, `/remove-appointment N`) or uses
`/delete-all`; MEMORA says this when consent is revoked. Deletion and `/export` are always
available.

## Deletion (`/delete-all`, typed confirmation)
Removes: facts, episodes, people and their face data, object sightings, care items and events,
interaction/feedback records, preferred name, safety contacts, consent decisions, MEMORA's log
files (`memora.log*`, `chat_debug.log`), and in-memory session state. Not removed: backups the
person made with `--backup` (they are told), and data already copied elsewhere. Deleted files
may remain recoverable on disk until overwritten (no secure erase).
