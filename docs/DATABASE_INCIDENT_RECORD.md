# Database Incident and Recovery Decision Record (F-04)

_Verified 2026-10-21 by read-only inspection. No file listed here was modified, restored, moved
or re-permissioned during verification. Comparisons ran on disposable copies (since removed)
and print only counts and hashes, never record contents._

## What happened
On 2026-10-21 at 06:01:48 an engineering run of `python app.py --check` without
`MEMORA_DB_PATH` opened the project-folder database with the full database layer, which
applies schema migrations and restricts permissions. At the time, `--check` was believed to
be read-only. That belief was wrong, and the owner had asked that this database not be
migrated. The cause was fixed in `5f753f6`: `--check` now inspects a temporary copy and never
creates a database (`tests/test_database_resolution.py::test_check_never_modifies_or_creates_the_user_database`).

## Files (verified)
| File | Size | Mode | Modified | SHA-1 | SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Live: `/Users/siddhant_patil/Projects/Samsung_Anchor/memora_db_v2.sqlite` | 122,880 | 0600 | 2026-10-21 06:01:48 | `972ed94334375c89914741490a5abe9d01a30d93` | `f63b943c978ffaf5a36baba602ff2d7a7c2f8a94367afa14b85b59a0d5bcf7dc` |
| Pre-incident copy: `~/memora_backups/20261021_pre-check-incident/memora_db_v2.sqlite` | 110,592 | 0600 | 2026-10-20 15:15:52 | `26f38093ce3733059f0c8b016fb172b5ea646fe6` | `0dd8a4469daf554c7d06418e4d863b8450618bb18662251ce780c38955eba091` |
| Owner's pre-work backup: `~/memora_backups/20261020/memora_db_v2.sqlite` (29 Sep state) | 110,592 | 0644 | 2026-09-29 00:50:20 | `d8d8ccd735c9d6d99849acda6dca305be24af407` | `74f58a430a7f3e149abc9b5468609a4cd7bfaf1adcb54831369667e73b7c900e` |

**Provenance of the pre-incident copy.** It was copied from `/private/tmp/db_before_tests.sqlite`,
taken on 2026-10-20 at 15:15:52. Four independent copies made on 2026-10-20 (15:15, 15:22,
16:31, 16:47) all have the same SHA-1 and SHA-256. That SHA-1, `26f38093…`, is the value
recorded throughout `PROJECT_STATE.md` and `docs/EXECUTION_LEDGER.md` before the incident.
**Conclusion:** the pre-incident copy is byte-identical to the live file as it was immediately
before the incident. Its mode is 0600, whereas the original live file was 0644.

## Differences: live vs pre-incident (row-level, disposable copies)
| Aspect | Result |
| :--- | :--- |
| SQLite `integrity_check` | `ok` for all three files |
| Rows in every original table (episodes 131, identities 27, relevant_memories 7, object_history 100, objects 2, five empty tables) | **identical**: same counts and same hash over all original columns |
| `system_state` | the two original rows are identical; one row added: `schema_version = 1` |
| Added tables | `care_items`, `care_events`, both empty |
| Added columns | `objects.source`, `object_history.source`, empty (NULL) in every row |
| Permissions | 0644 → 0600 |
| Log | 6 metadata lines (paths, "Applied schema migrations") appended to `data/logs/memora.log`; no conversation content |

No personal record was added, changed or removed.

## In use?
`lsof` shows no process with the live file open. The only running process with "app" in its
command line is a Streamlit app whose working directory is `~/Projects/SlotSmith`, an
unrelated project.

## Options (the owner decides; nothing has been done)
| Option | Result | Consequences |
| :--- | :--- | :--- |
| A. Keep the migrated file (no action) | All data intact; file now has the newer schema | An older MEMORA build can still read it (migrations are additive). Any future `--chat` or runtime use would have migrated it anyway |
| B. Restore the exact pre-incident file | Byte-identical to the 20 Oct state | Undoes the incident exactly. The next `--chat` or runtime use against this path migrates it again |
| C. Leave it as an archive; use a fresh database for real use | Recommended for real use regardless of A/B | The file contains synthetic test contamination (C2-24); `deployment/create_dev_database.py` creates a clean one |

**Engineering recommendation:** B if you want the archive exactly as it was before this work;
otherwise A. In both cases C for any real use.

## Exact restoration procedure (option B, only with the owner's approval)
```bash
cd /Users/siddhant_patil/Projects/Samsung_Anchor
lsof memora_db_v2.sqlite                      # must print nothing (MEMORA not running)
mkdir -m 700 ~/memora_backups/20261021_migrated-state     # keep the migrated file too
cp -p memora_db_v2.sqlite ~/memora_backups/20261021_migrated-state/
shasum -a 256 ~/memora_backups/20261021_migrated-state/memora_db_v2.sqlite   # expect f63b943c…
cp -p ~/memora_backups/20261021_pre-check-incident/memora_db_v2.sqlite memora_db_v2.sqlite
shasum -a 256 memora_db_v2.sqlite             # expect 0dd8a4469daf554c…
chmod 644 memora_db_v2.sqlite                 # optional: the original mode was 0644
```
Afterwards, do not run `--chat` or the runtime without `MEMORA_DB_PATH` set to another
location, or the file will be migrated again. The 6 log lines can stay; they contain no
personal content. All three copies (migrated, pre-incident and the 29 Sep backup) remain.
