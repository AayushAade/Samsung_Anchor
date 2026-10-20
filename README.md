# MEMORA

MEMORA is a privacy-first memory assistant for people with memory difficulties,
with Alzheimer's care as a central use case. It remembers what a person tells it,
answers questions about it honestly (with when it was told), keeps a history of
corrections, and directs the person to human help when something sounds urgent.

```
Stage:     Development (not yet internal alpha)
Verified:  text conversation, memory with provenance, restart persistence,
           data view/export/delete, urgent-statement guidance, simulation,
           clean install (macOS arm64), container (linux/arm64)
Not yet verified: real camera, microphone, voice output, face recognition,
           object detection, live Gemini API, long-duration stability
```

MEMORA is **not a medical device**. It does not diagnose, give medication advice,
monitor emergencies, or contact anyone. See
[CAPABILITY_VERIFICATION_MATRIX.md](CAPABILITY_VERIFICATION_MATRIX.md) for exactly
what has been verified and how.

## Quick start

Requires Python 3.11.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py --chat
```

Example conversation:

```
MEMORA: Hello, I'm MEMORA, a memory assistant. What would you like me to call you?
You: My name is Sid
MEMORA: Nice to meet you, Sid. I'll call you Sid.
You: My daughter is Riya
MEMORA: I'll remember that your daughter is Riya.
...next day, after a restart...
You: Who is my daughter?
MEMORA: You told me yesterday that your daughter is Riya.
```

Chat commands: `/memories`, `/forget N`, `/people`, `/objects`, `/export [file]`,
`/delete-all`, `/status`, `/quit`.

### Where data is stored

- Default database: `memora_db_v2.sqlite` in the project folder (face data alongside as
  `memora_db_v2.faces.json`). Override with `MEMORA_DB_PATH=/path/to/memora.sqlite`.
- `--simulation` and `--scenario` use a separate database under `data/simulation/`.
- Nothing is sent to a cloud service in `--chat` mode.

## Other commands

| Command | Purpose |
| :--- | :--- |
| `python app.py --check` | Diagnostics: dependencies, database integrity, optional capabilities (does not open the camera) |
| `python app.py --simulation --validate-runtime --max-cycles 25` | Run the continuous runtime with simulated sensors and print measured statistics |
| `python app.py --scenario` | Run the synthetic clinical-behaviour scenarios against their specifications |
| `python inspect_database.py [db]` | Inspect stored data and SQLite/face-data consistency |
| `python app.py --live-hardware` | Continuous runtime with camera/microphone (**unverified**; requires `requirements-hardware.txt`) |

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
- [docs/LICENSING_REVIEW.md](docs/LICENSING_REVIEW.md), [docs/product/PRODUCT_SPEC.md](docs/product/PRODUCT_SPEC.md)

Documents under `docs/certification/` and earlier "RC1 certified" claims are
historical and are **not supported by current evidence**; see the documentation
index in PROJECT_STATE.md.

## License

No license has been chosen yet (originally a Samsung Solve For Tomorrow competition
entry). See [docs/LICENSING_REVIEW.md](docs/LICENSING_REVIEW.md).
