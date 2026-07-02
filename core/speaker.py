import subprocess
import threading
import sys

class MemoraSpeaker:
    """
    Pillar I & II Output Module: Text-To-Speech (TTS).
    Uses native platform commands (say on macOS, System.Speech on Windows, spd-say on Linux)
    to speak cues out loud without adding heavy Python dependencies (like pyttsx3 or pywin32).
    """
    def __init__(self):
        self.platform = sys.platform

    def speak(self, text, wait=False):
        """
        Synthesizes text to speech using native system synthesis.
        If wait is False, it speaks asynchronously in a background thread to prevent blocking the frame loop.
        """
        if not text:
            return
            
        def _run_speak():
            try:
                if self.platform == "darwin":  # macOS
                    # 'say' is standard and pre-installed on macOS
                    subprocess.run(["say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif self.platform == "win32":  # Windows
                    cleaned_text = text.replace('"', '\\"')
                    ps_command = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{cleaned_text}")'
                    subprocess.run(["powershell", "-Command", ps_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:  # Linux / fallback
                    subprocess.run(["spd-say", text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"\n[Speaker Warning] Failed to output speech: {e}")
                
        if wait:
            _run_speak()
        else:
            threading.Thread(target=_run_speak, daemon=True).start()
