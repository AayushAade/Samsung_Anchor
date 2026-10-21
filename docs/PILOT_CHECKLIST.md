# Supervised Technical Pilot — Checklist (not yet executed)

_Prepared 2026-10-21. This is a checklist, not an authorisation: no participant has used
MEMORA. A pilot may start only when the owner has approved it in writing and every
"Before" item is ticked. Scope: the **text product** (`python app.py --chat` or the Docker
image) only. No camera, microphone, face recognition, cloud features or hardware._

## What a technical pilot can and cannot show
- **Can show:** installation works on participants' machines; conversations, corrections,
  reminders, export and deletion behave as tested; where the rule-based phrasing fails.
- **Cannot show:** clinical benefit or safety, suitability for unsupervised use, or regulatory
  compliance. Participants must not rely on MEMORA for medication, safety or emergencies.

## Before the pilot
**Authorisation and governance**
- [ ] Owner approval in writing: purpose, dates, number of participants, named supervisor.
- [ ] Decision on whether ethics review applies (institution/country). If participants have
      memory difficulties, assume it does until a qualified person says otherwise.
- [ ] Repository licence (or a pilot agreement) settled, so participants have the right to use
      the software (`docs/LICENSING_REVIEW.md` D6).
- [ ] Privacy review of what is stored (`docs/PRIVACY_AND_CONSENT.md`), where, for how long,
      and who can see it; data-protection notice written in plain language.
- [ ] Named person responsible for safety, reachable during the pilot.

**Participants**
- [ ] Adults able to give informed consent themselves. Participants with memory difficulties
      only after ethics approval and with a carer present.
- [ ] Written consent covering: MEMORA is experimental, not a medical device, keeps data
      only on their computer, can be stopped and all data deleted at any time.
- [ ] Synthetic or non-sensitive content encouraged; no real medication schedules unless a
      carer double-checks them independently.

**Installation (per machine)**
- [ ] Core install only (`requirements.txt`) or the Docker image; **not** `requirements-hardware.txt` or `requirements-cloud.txt`.
- [ ] `MEMORA_*` network variables unset; `python app.py --check` shows "Network Use: PASS Nothing".
- [ ] Separate data folder created with `python deployment/create_dev_database.py <folder>`.
- [ ] Emergency number set with `/set-emergency-number`; trusted contact if the participant wants.
- [ ] A verified backup with `python app.py --backup <folder>` before the first session.

## During the pilot
- [ ] Supervisor checks in at an agreed interval (e.g. daily at first).
- [ ] Incident log: any wrong recall, invented fact, missed urgent phrase, confusing reply,
      crash, or data problem; date, what was typed (with consent) and what MEMORA replied.
- [ ] Stop rule: any reply that could cause harm (e.g. wrong medication information, a missed
      urgent statement) pauses the pilot for that participant until reviewed.
- [ ] No software updates mid-pilot without recording the commit and re-running the checks.

## After the pilot
- [ ] Offer each participant `/export` and `/delete-all`; record that deletion was confirmed.
- [ ] Summarise incidents and phrasing failures; add regression tests for each software defect.
- [ ] Record results in `docs/evidence/` without personal content.
- [ ] Do not describe results as clinical evidence.
