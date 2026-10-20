"""
MEMORA text conversation mode.

A person types; MEMORA answers through the same cognitive pipeline used by the
continuous runtime. Camera and microphone are off in this mode, so nothing is
observed: everything MEMORA knows here comes from what the person typed.

Internal diagnostic output from the pipeline is written to a log file rather
than mixed into the conversation.
"""

from __future__ import annotations

import contextlib
import io
import os
from datetime import datetime
from typing import Any, Callable, Optional

from config import settings
from config.paths import DATA_DIR
from src.memory import user_data

HELP_TEXT = """Commands:
  /memories        Show what you have told me (numbered)
  /forget N        Permanently delete memory number N
  /medications                         List medication schedules
  /add-medication NAME at HH:MM [, DOSE]  e.g. /add-medication Aspirin at 08:00, 75 mg
  /remove-medication N
  /appointments                        List upcoming appointments
  /add-appointment TITLE on YYYY-MM-DD HH:MM [at PLACE]
  /remove-appointment N
  /set-emergency-number NUMBER          e.g. /set-emergency-number 911
  /set-trusted-contact NAME PHONE      e.g. /set-trusted-contact Riya 555-0100
  /people          Show people I know
  /objects         Show where I last saw things
  /export [file]   Save a copy of everything I store about you (JSON)
  /delete-all      Permanently delete everything I store about you
  /status          Show what is on, off, and where data is saved
  /quit            Exit
Anything else is treated as something you are saying to me."""


class ChatSession:
    def __init__(self, coordinator: Any, log_path: Optional[str] = None,
                 confirm: Optional[Callable[[str], str]] = None) -> None:
        self.coordinator = coordinator
        self.pipeline = coordinator.pipeline
        self.db = coordinator.database
        self.log_path = log_path or str(DATA_DIR / "logs" / "chat_debug.log")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        # The debug log contains what the person typed: owner-only access.
        if not os.path.exists(self.log_path):
            os.close(os.open(self.log_path, os.O_WRONLY | os.O_CREAT, 0o600))
        os.chmod(self.log_path, 0o600)
        self.confirm = confirm or input
        self._numbered_facts: list[dict] = []

    # ------------------------------------------------------------------

    def _quietly(self, fn, *args, **kwargs):
        """Run pipeline code with its console diagnostics redirected to the log file."""
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                return fn(*args, **kwargs)
        finally:
            text = buf.getvalue()
            if text:
                with open(self.log_path, "a") as f:
                    f.write(f"\n--- {datetime.now().isoformat()} ---\n{text}")

    def status_lines(self) -> list[str]:
        integrity = self.db.check_integrity()
        mem = "OK" if integrity["ok"] else "needs attention (see /status details below)"
        lines = [
            f"Saving memories to: {self.db.db_path or 'temporary memory (lost on exit)'}",
            "Camera: off    Microphone: off (you type)    Voice output: off",
            "Cloud AI: not used in this mode. Replies come from rules on this computer.",
            f"Memory store: {mem}",
        ]
        if integrity["identities_without_embeddings"]:
            lines.append(f"  {len(integrity['identities_without_embeddings'])} stored people have no face data "
                         "and cannot be recognised until re-enrolled.")
        for key in ("vector_store_load_error", "vector_store_save_error"):
            if integrity.get(key):
                lines.append(f"  {integrity[key]}")
        return lines

    def opening(self) -> str:
        name = self.pipeline.conversational_memory.get_preferred_name()
        if name:
            reminder = self._quietly(self.pipeline.due_reminder_message, name)
            return f"Welcome back, {name}. How can I help?" + (f"\n{reminder}" if reminder else "")
        return ("Hello, I'm MEMORA, a memory assistant. What would you like me to call you? "
                "You can say: My name is ...")

    # ------------------------------------------------------------------

    def handle(self, line: str) -> Optional[str]:
        """Process one line of input. Returns the reply, or None to end the session."""
        text = (line or "").strip()
        if not text:
            return ""
        if text.startswith("/"):
            return self._command(text)
        result = self._quietly(self.pipeline.process, user_speech=text, return_dict=True)
        if getattr(self.pipeline, "last_cycle_error", None):
            return ("Sorry, something went wrong on my side, so I may not have saved or understood that. "
                    f"Details were written to {self.log_path}.")
        reply = result.get("speech_response") or "I'm here."
        if self.pipeline.current_patient_state.mode.name != "EMERGENCY":
            reminder = self._quietly(self.pipeline.due_reminder_message, self.pipeline._patient_name())
            if reminder:
                reply += "\n" + reminder
        return reply

    def _command(self, text: str) -> Optional[str]:
        cmd, _, arg = text.partition(" ")
        cmd, arg = cmd.lower(), arg.strip()
        if cmd in ("/quit", "/exit", "/q"):
            return None
        if cmd == "/help":
            return HELP_TEXT
        if cmd == "/status":
            return "\n".join(self.status_lines())
        if cmd in ("/memories", "/facts"):
            self._numbered_facts = user_data.list_facts(self.db)
            if not self._numbered_facts:
                return "You haven't told me anything to remember yet."
            rows = []
            for i, f in enumerate(self._numbered_facts, 1):
                when = (f["recorded_at"] or "")[:16].replace("T", " ")
                note = "" if f["status"] == "active" else "   (replaced by a newer statement)"
                rows.append(f"  {i}. \"{f['statement']}\" - you told me {when}{note}")
            return "What you've told me:\n" + "\n".join(rows) + "\nUse /forget N to delete one."
        if cmd == "/forget":
            if not self._numbered_facts:
                self._numbered_facts = user_data.list_facts(self.db)
            if not arg.isdigit() or not 1 <= int(arg) <= len(self._numbered_facts):
                return "Please give the number shown by /memories, for example: /forget 2"
            fact = self._numbered_facts[int(arg) - 1]
            ok = user_data.delete_fact(self.db, fact["id"])
            self._numbered_facts = []
            return (f"Deleted: \"{fact['statement']}\"." if ok
                    else "I couldn't delete that memory. Nothing was changed.")
        if cmd in ("/medications", "/add-medication", "/remove-medication",
                   "/appointments", "/add-appointment", "/remove-appointment"):
            return self._care_command(cmd, arg)
        if cmd in ("/set-emergency-number", "/set-trusted-contact"):
            return self._safety_setting(cmd, arg)
        if cmd == "/people":
            people = user_data.list_people(self.db)
            if not people:
                return "I don't know anyone yet."
            return "\n".join(f"  {p['name'] or 'Unnamed person'}"
                             f"{' (' + p['relationship'] + ')' if p['relationship'] else ''}"
                             f" - last seen {(p['last_seen'] or 'never')[:16].replace('T', ' ')}" for p in people)
        if cmd == "/objects":
            objects = user_data.list_objects(self.db)
            if not objects:
                return "I haven't seen any of your things yet."
            return "\n".join(f"  {o['name']}: last seen in {o['room']} at "
                             f"{(o['last_seen'] or '')[:16].replace('T', ' ')}" for o in objects)
        if cmd == "/export":
            path = arg or str(DATA_DIR / "exports" / f"memora_export_{datetime.now():%Y%m%d_%H%M%S}.json")
            try:
                written = user_data.write_export(self.db, path)
            except OSError as e:
                return f"Export failed: {e}"
            return f"Saved a copy of your data to {written}"
        if cmd == "/delete-all":
            answer = self.confirm("This permanently deletes everything I store about you. "
                                  "Type DELETE to confirm: ")
            if answer.strip() != "DELETE":
                return "Cancelled. Nothing was deleted."
            report = user_data.delete_all_user_data(self.db)
            self.pipeline.conversational_memory.search_history.clear()
            return ("All your data has been deleted." if report["ok"]
                    else f"Deletion was incomplete. Remaining records: {report['remaining']}")
        return f"I don't know the command {cmd}. Type /help to see the commands."

    def _safety_setting(self, cmd: str, arg: str) -> str:
        import re
        from src.cognition.conversational_memory import EMERGENCY_NUMBER_KEY, TRUSTED_CONTACT_KEY
        if cmd == "/set-emergency-number":
            if not re.fullmatch(r"\+?[0-9][0-9 \-]{1,19}", arg):
                return "Please give a number, for example: /set-emergency-number 911"
            self.db._set_system_state(EMERGENCY_NUMBER_KEY, arg)
            return f"Saved. If something sounds urgent I'll tell you to call {arg}. I can't make calls myself."
        m = re.fullmatch(r"([A-Za-z][A-Za-z .'\-]{0,40}?)\s+(\+?[0-9][0-9 \-]{3,19})", arg)
        if not m:
            return "Please give a name and phone number, for example: /set-trusted-contact Riya 555-0100"
        contact = f"{m.group(1).strip()} on {m.group(2).strip()}"
        self.db._set_system_state(TRUSTED_CONTACT_KEY, contact)
        return f"Saved. In an urgent situation I'll also suggest calling {contact}. I can't make calls myself."

    def _care_command(self, cmd: str, arg: str) -> str:
        import re
        meds = self.pipeline.medication_mgr
        appts = self.pipeline.appointment_mgr
        if cmd == "/medications":
            items = meds.get_all_schedules()
            if not items:
                return "No medication schedules recorded. Add one with /add-medication NAME at HH:MM"
            return "\n".join(f"  {i}. {m.medication_name}{' (' + m.dose + ')' if m.dose else ''} daily at "
                             f"{m.scheduled_time}{' - you told me you took it today' if meds.reported_taken_today(m.med_id) else ''}"
                             for i, m in enumerate(items, 1))
        if cmd == "/add-medication":
            m = re.match(r"^(.+?)\s+at\s+(\d{1,2}:\d{2}(?:\s*[ap]m)?)\s*(?:,\s*(.+))?$", arg, re.IGNORECASE)
            if not m:
                return "Please use: /add-medication NAME at HH:MM [, DOSE]"
            time_str = m.group(2).upper().replace("AM", " AM").replace("PM", " PM").replace("  ", " ")
            try:
                sched = meds.add_scheduled(m.group(1).strip(), time_str.strip(), (m.group(3) or "").strip())
            except ValueError as e:
                return str(e)
            return (f"Saved: {sched.medication_name} daily at {sched.scheduled_time}. I'll give a gentle reminder "
                    "if it's past that time and you haven't told me you took it.")
        if cmd == "/remove-medication":
            items = meds.get_all_schedules()
            if not arg.isdigit() or not 1 <= int(arg) <= len(items):
                return "Please give the number shown by /medications."
            target = items[int(arg) - 1]
            return f"Removed {target.medication_name}." if meds.remove_medication(target.med_id) else "Nothing was removed."
        if cmd == "/appointments":
            items = appts.get_upcoming_appointments()
            if not items:
                return "No upcoming appointments recorded."
            return "\n".join(f"  {i}. {a.title} {a.scheduled_time}{' at ' + a.location if a.location else ''}"
                             for i, a in enumerate(items, 1))
        if cmd == "/add-appointment":
            m = re.match(r"^(.+?)\s+on\s+(\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2})(?:\s+at\s+(.+))?$", arg)
            if not m:
                return "Please use: /add-appointment TITLE on YYYY-MM-DD HH:MM [at PLACE]"
            try:
                when = datetime.fromisoformat(m.group(2).replace(" ", "T"))
            except ValueError:
                return "That date or time isn't valid. Example: 2026-11-03 10:30"
            appt = appts.add_scheduled(m.group(1).strip(), when, (m.group(3) or "").strip())
            return f"Saved: {appt.title} {appt.scheduled_time}{' at ' + appt.location if appt.location else ''}."
        if cmd == "/remove-appointment":
            items = appts.get_upcoming_appointments()
            if not arg.isdigit() or not 1 <= int(arg) <= len(items):
                return "Please give the number shown by /appointments."
            target = items[int(arg) - 1]
            return f"Removed {target.title}." if appts.remove_appointment(target.appt_id) else "Nothing was removed."
        return ""

    # ------------------------------------------------------------------

    def run(self, read: Callable[[str], str] = input, write: Callable[[str], None] = print) -> None:
        write("=" * 64)
        write("MEMORA - memory assistant (text conversation)")
        for line in self.status_lines():
            write("  " + line)
        write("  Type /help for commands, /quit to exit.")
        write("=" * 64)
        write(f"MEMORA: {self.opening()}")
        try:
            while True:
                try:
                    line = read("You: ")
                except EOFError:
                    break
                reply = self.handle(line)
                if reply is None:
                    break
                if reply:
                    write(f"MEMORA: {reply}")
        except KeyboardInterrupt:
            write("")
        finally:
            self.close()
            write("MEMORA: Goodbye.")

    def close(self) -> None:
        self._quietly(self.pipeline.shutdown)
        self.db.close()


def run_chat() -> None:
    from src.application.factory import build_application

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        coordinator = build_application(live_hardware=False)
    session = ChatSession(coordinator)
    with open(session.log_path, "a") as f:
        f.write(f"\n--- startup {datetime.now().isoformat()} (DB: {settings.DB_PATH}) ---\n{buf.getvalue()}")
    session.run()
