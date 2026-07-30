import speech_recognition as sr
import sys
import struct
from src.utils.event_logger import log_event
from config import settings

class MemoraAudioListener:
    def __init__(self, duration_sec=5, mock_mode=False, device_index=None):
        self.duration_sec = duration_sec
        self.mock_mode = mock_mode
        self.recognizer = sr.Recognizer()
        self.device_index = device_index
        
        # Test if microphone is accessible
        if not self.mock_mode and self.device_index is None:
            try:
                mics = sr.Microphone.list_microphone_names()
                if not mics:
                    if settings.DEBUG:
                        print("[Audio Listener Warning] No microphone devices found. Enabling typing fallback mode.")
                    self.mock_mode = True
                else:
                    for idx, name in enumerate(mics):
                        name_lower = name.lower()
                        if "microphone array" in name_lower or "mic array" in name_lower:
                            self.device_index = idx
                            if settings.DEBUG:
                                print(f"[Audio Listener] Auto-selected Microphone Array at index {idx}: {name}")
                            break
                    
                    if self.device_index is None:
                        for idx, name in enumerate(mics):
                            name_lower = name.lower()
                            if "microphone" in name_lower or "mic" in name_lower:
                                if "sound mapper" not in name_lower and "stereo mix" not in name_lower:
                                    self.device_index = idx
                                    if settings.DEBUG:
                                        print(f"[Audio Listener] Auto-selected Microphone at index {idx}: {name}")
                                    break
                                    
                    if self.device_index is None:
                        self.device_index = 0
                        if settings.DEBUG:
                            print(f"[Audio Listener] Using default microphone at index 0: {mics[0]}")
                        
            except Exception as e:
                if settings.DEBUG:
                    print(f"[Audio Listener Warning] Microphone check failed: {e}. Enabling typing fallback mode.")
                self.mock_mode = True
        elif self.device_index is not None:
            if settings.DEBUG:
                print(f"[Audio Listener] Using user-specified microphone index: {self.device_index}")

    def listen_and_transcribe(self):
        """
        Listens to ambient audio for self.duration_sec seconds and transcribes it.
        If mock_mode is True, prompts the user to type in the terminal instead.
        Returns:
            str: The transcribed text, or None if transcription failed.
        """
        if self.mock_mode:
            log_event("audio_start", "Audio listening started (typing simulation)...")
            try:
                text = input("> ")
                if not text.strip():
                    return None
                log_event("transcript", f"Transcript received: \"{text}\"")
                return text
            except (KeyboardInterrupt, EOFError):
                return None

        # Real microphone capture
        try:
            with sr.Microphone(device_index=self.device_index) as source:
                self.recognizer.energy_threshold = 150
                self.recognizer.dynamic_energy_threshold = True
                
                if settings.DEBUG:
                    print(f"\n[Microphone] Adjusting for ambient noise... (0.5 seconds)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                log_event("audio_start", f"Audio listening started (Microphone index {self.device_index}). Speak now!")
                audio = self.recognizer.listen(source, timeout=self.duration_sec + 2, phrase_time_limit=self.duration_sec)
                
                # Silence Check
                try:
                    raw_data = audio.get_raw_data()
                    count = len(raw_data) // 2
                    if count > 0:
                        shorts = struct.unpack(f"{count}h", raw_data)
                        max_amplitude = max(abs(s) for s in shorts)
                        if max_amplitude < 100:  # Practically silent
                            print(f"\n[Microphone Warning] The captured audio was completely silent (Max Amplitude: {max_amplitude}).")
                            print("On macOS, please check: System Settings -> Privacy & Security -> Microphone (Allow Terminal/Python).")
                except Exception:
                    pass
                
                if settings.DEBUG:
                    print("[Microphone] Processing audio...")
                transcription = self.recognizer.recognize_google(audio)
                log_event("transcript", f"Transcript received: \"{transcription}\"")
                return transcription
        except sr.WaitTimeoutError:
            if settings.DEBUG:
                print("[Microphone Warning] No speech was detected (timeout).")
            return None
        except sr.UnknownValueError:
            if settings.DEBUG:
                print("[Microphone Warning] Speech was detected but could not be understood. Switching to manual typing fallback.")
            self.mock_mode = True
            return self.listen_and_transcribe()
        except sr.RequestError as e:
            if settings.DEBUG:
                print(f"[Microphone Error] Google Speech Recognition service requested error: {e}. Switching to typing.")
            self.mock_mode = True
            return self.listen_and_transcribe()
        except Exception as e:
            if settings.DEBUG:
                print(f"[Microphone Error] An unexpected error occurred: {e}. Switching to typing.")
            self.mock_mode = True
            return self.listen_and_transcribe()
