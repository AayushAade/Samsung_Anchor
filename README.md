# MEMORA

MEMORA is a privacy-first memory assistant for people with memory difficulties,
with Alzheimer's care as a central use case. It remembers what a person tells it,
answers questions about it honestly (with when it was told), keeps a history of
corrections, and directs the person to human help when something sounds urgent.

```
Stage:     Development (not yet internal alpha)
Verified:  text conversation with consent, memory with provenance and
           corrections, reminders/appointments, restart persistence, data
           view/export/delete, backup/restore, urgent-statement guidance,
           where you said you put things, 20 simulated journeys, clean
           install (Python 3.11-3.13), Docker, CI (Linux)
Not yet verified: real camera, microphone, voice output, object
           detection, live Gemini API, long-duration stability
Face recognition: OpenCV YuNet + SFace backend implemented and tested with
           synthetic stand-ins; inactive until the owner provisions model files
           (none shipped or downloaded); never tested on a camera
           (docs/FACE_RECOGNITION.md)
```

MEMORA is **not a medical device**. It does not diagnose, give medication advice,
monitor emergencies, or contact anyone. See
[CAPABILITY_VERIFICATION_MATRIX.md](CAPABILITY_VERIFICATION_MATRIX.md) for exactly
what has been verified and how.

## Quick start

Requires Python 3.11, 3.12 or 3.13 (core install verified on all three).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py --chat
```

Example conversation:

```
MEMORA: Hello, I'm MEMORA, a memory assistant. Before we start: may I save what you
        tell me, on this computer only, so I can remind you later? ... Please answer yes or no.
You: yes
MEMORA: Thank you. I'll save what you tell me on this computer. What would you like me to call you?
You: My name is Sid
MEMORA: Nice to meet you, Sid. I'll call you Sid.
You: My daughter is Riya
MEMORA: I'll remember that your daughter is Riya.
...next day, after a restart...
You: Who is my daughter?
MEMORA: You told me yesterday that your daughter is Riya.
```

On first run MEMORA asks whether it may save what you tell it; nothing is stored
until you agree (`/consent` shows or changes this at any time).

Chat commands (`/help` lists them all): `/memories`, `/forget N`, `/medications`,
`/add-medication`, `/appointments`, `/add-appointment`, `/set-emergency-number`,
`/set-trusted-contact`, `/people`, `/objects`, `/export [file]`, `/delete-all`,
`/consent`, `/status`, `/quit`.

### A separate development database

```bash
python deployment/create_dev_database.py ~/memora-data/dev
export MEMORA_DB_PATH=~/memora-data/dev/memora.sqlite MEMORA_LOG_DIR=~/memora-data/dev/logs
```
The tool refuses to touch an existing database. Tests and `--simulate` always use their own
temporary storage.

### Where data is stored

- Default database: `memora_db_v2.sqlite` in the project folder (face data alongside as
  `memora_db_v2.faces.json`). Override with `MEMORA_DB_PATH=/path/to/memora.sqlite`;
  unless that exact file already exists, MEMORA stores it as `/path/to/memora_v2.sqlite`
  (`--check` and `/status` show the file actually used).
- `--simulation` and `--scenario` use a separate database under `data/simulation/`.
- `--chat`, `--simulate` and the default runtime make **no network connections** (enforced by
  `tests/test_network_policy.py`, which intercepts sockets). Features that can contact the internet
  are off unless explicitly enabled: `MEMORA_ALLOW_MODEL_DOWNLOAD=1` (speech-model download),
  `MEMORA_ALLOW_CLOUD_ASR=1` (Google speech recognition of microphone audio),
  `MEMORA_ALLOW_CLOUD_LLM=1` with `GEMINI_API_KEY` (Gemini name extraction). `--check` and
  `/status` report what is enabled. See `docs/PRIVACY_AND_CONSENT.md`.

## Other commands

| Command | Purpose |
| :--- | :--- |
| `python app.py --check` | Read-only diagnostics: dependencies, database integrity (checked on a temporary copy), optional capabilities, network use (does not open the camera) |
| `python app.py --simulation --validate-runtime --max-cycles 25` | Run the continuous runtime with simulated sensors and print measured statistics |
| `python app.py --scenario` | Run the synthetic clinical-behaviour scenarios against their specifications |
| `python app.py --simulate [NAME ...]` | Run 20 deterministic simulated user journeys in isolated temporary storage (simulated clock, battery, sensors) |
| `python app.py --backup [DIR]` / `--restore DIR` | Verified backup / restore of the memory database |
| `python app.py --repair` | Remove people records that have no face data (asks first, backs up first) |
| `python inspect_database.py [db]` | Inspect stored data and SQLite/face-data consistency |
| `python app.py --live-hardware` | Continuous runtime with camera/microphone (**unverified**; requires `requirements-hardware.txt`; see [docs/HARDWARE_TEST_CHECKLIST.md](docs/HARDWARE_TEST_CHECKLIST.md)). Real devices are used **only** with this flag |

Optional extras: `requirements-hardware.txt` (sensors and on-device models — check
[licensing](docs/LICENSING_REVIEW.md) first), `requirements-cloud.txt` (Gemini, used
only for name extraction during identity learning), `requirements-dev.txt` (tests).

## Docker

```bash
docker build -t memora -f deployment/docker/Dockerfile .
docker run -it -v memora-data:/data memora            # chat
docker run --rm -v memora-data:/data memora python app.py --check
```

Personal data lives only in the `/data` volume.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

The suite runs against a temporary database (see `tests/conftest.py`) and never
touches your real data. Latest result: see [PROJECT_STATE.md](PROJECT_STATE.md).

## Documentation

- [PROJECT_STATE.md](PROJECT_STATE.md) — current verified state, commands, test baseline, documentation index
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) — how the code actually runs
- [CAPABILITY_VERIFICATION_MATRIX.md](CAPABILITY_VERIFICATION_MATRIX.md) — evidence per capability
- [MASTER_ROADMAP.md](MASTER_ROADMAP.md) — prioritised next work and release stages
- [docs/SAFETY_AND_LIMITATIONS.md](docs/SAFETY_AND_LIMITATIONS.md) — safety design, policy decisions, what is not verified
- [docs/LICENSING_REVIEW.md](docs/LICENSING_REVIEW.md), [docs/product/PRODUCT_SPEC.md](docs/product/PRODUCT_SPEC.md)
- [docs/EXECUTION_LEDGER.md](docs/EXECUTION_LEDGER.md) — engineering findings log
- [docs/RELEASE_GATES.md](docs/RELEASE_GATES.md) — release gates and readiness by use
- [docs/HARDWARE_TEST_CHECKLIST.md](docs/HARDWARE_TEST_CHECKLIST.md), [docs/PILOT_CHECKLIST.md](docs/PILOT_CHECKLIST.md) — prepared, not executed

Documents under `docs/certification/` and earlier "RC1 certified" claims are
historical and are **not supported by current evidence**; see the documentation
index in PROJECT_STATE.md.

## License

No license has been chosen yet (originally a Samsung Solve For Tomorrow competition
entry). See [docs/LICENSING_REVIEW.md](docs/LICENSING_REVIEW.md).
