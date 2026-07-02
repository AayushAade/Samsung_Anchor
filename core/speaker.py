import subprocess
import threading

class MemoraSpeaker:
    """
    Pillar I & II Output Module: Text-To-Speech (TTS).
    Uses Windows native SpeechSynthesizer via PowerShell to speak cues
    out loud without adding heavy Python dependencies (like pyttsx3 or pywin32).
    """
    def __init__(self):
        pass

    def speak(self, text, wait=False):
        """
        Synthesizes text to speech using Windows native System.Speech synthesizer.
        If wait is False, it speaks asynchronously in a background thread to prevent blocking the frame loop.
        """
        if not text:
            return
            
        cleaned_text = text.replace('"', '\\"')
        
        def _run_speak():
            ps_command = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{cleaned_text}")'
            subprocess.run(["powershell", "-Command", ps_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        if wait:
            _run_speak()
        else:
            threading.Thread(target=_run_speak, daemon=True).start()
