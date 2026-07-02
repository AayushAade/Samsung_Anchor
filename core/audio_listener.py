import speech_recognition as sr
import sys
import struct

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
                    print("[Audio Listener Warning] No microphone devices found. Enabling typing fallback mode.")
                    self.mock_mode = True
                else:
                    # Find the best physical microphone (built-in Microphone Array or physical Mic)
                    for idx, name in enumerate(mics):
                        name_lower = name.lower()
                        if "microphone array" in name_lower or "mic array" in name_lower:
                            self.device_index = idx
                            print(f"[Audio Listener] Auto-selected Microphone Array at index {idx}: {name}")
                            break
                    
                    if self.device_index is None:
                        for idx, name in enumerate(mics):
                            name_lower = name.lower()
                            if "microphone" in name_lower or "mic" in name_lower:
                                if "sound mapper" not in name_lower and "stereo mix" not in name_lower:
                                    self.device_index = idx
                                    print(f"[Audio Listener] Auto-selected Microphone at index {idx}: {name}")
                                    break
                                    
                    if self.device_index is None:
                        self.device_index = 0
                        print(f"[Audio Listener] Using default microphone at index 0: {mics[0]}")
                        
            except Exception as e:
                print(f"[Audio Listener Warning] Microphone check failed: {e}. Enabling typing fallback mode.")
                self.mock_mode = True
        elif self.device_index is not None:
            print(f"[Audio Listener] Using user-specified microphone index: {self.device_index}")

    def listen_and_transcribe(self):
        """
        Listens to ambient audio from the microphone for the configured duration (default 5s)
        and transcribes it to text.
        If mock_mode is active or a device error occurs, prompts the user to type the phrase.
        Returns:
            str: The transcribed text, or None if transcription fails.
        """
        if self.mock_mode:
            print("\n>>> [Microphone Sim] Speak now (type your greeting/phrase and press Enter): ", end="")
            sys.stdout.flush()
            try:
                text = sys.stdin.readline().strip()
                if not text:
                    return None
                print(f"[Microphone Sim] Transcribed: \"{text}\"")
                return text
            except KeyboardInterrupt:
                return None
            except Exception as e:
                print(f"[Microphone Sim Error] Failed to read input: {e}")
                return None

        # Real microphone capture
        try:
            with sr.Microphone(device_index=self.device_index) as source:
                # Set a highly sensitive baseline energy threshold to ensure low voices are captured
                self.recognizer.energy_threshold = 150
                self.recognizer.dynamic_energy_threshold = True
                
                print(f"\n[Microphone] Adjusting for ambient noise... (0.5 seconds)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                print(f"[Microphone] Listening for {self.duration_sec} seconds... Speak now!")
                audio = self.recognizer.listen(source, timeout=self.duration_sec + 2, phrase_time_limit=self.duration_sec)
                
                # Silence / Mute Diagnostic Check
                try:
                    raw_data = audio.get_raw_data()
                    count = len(raw_data) // 2
                    if count > 0:
                        shorts = struct.unpack(f"{count}h", raw_data)
                        max_amplitude = max(abs(s) for s in shorts)
                        if max_amplitude < 100:  # Practically silent
                            print(f"\n[Microphone Warning] The captured audio was completely silent (Max Amplitude: {max_amplitude}).")
                            print("This usually means your physical microphone is MUTED at the OS level or BLOCKED by Windows Privacy Settings.")
                            print("Please check your Windows Privacy Settings: Settings -> Privacy -> Microphone (Allow apps to access microphone).")
                except Exception as diagnostic_err:
                    pass  # Don't block transcription if diagnostic fails
                
                print("[Microphone] Processing audio...")
                transcription = self.recognizer.recognize_google(audio)
                print(f"[Microphone] Transcribed: \"{transcription}\"")
                return transcription

        except sr.WaitTimeoutError:
            print("[Microphone Warning] No speech detected (timeout).")
            return None
        except sr.UnknownValueError:
            print("[Microphone Warning] Speech was detected but could not be understood.")
            print("Switching to manual typing fallback for this turn.")
            self.mock_mode = True
            return self.listen_and_transcribe()
        except sr.RequestError as e:
            print(f"[Microphone Error] Could not request results from Google Speech Recognition service; {e}")
            print("Switching to manual typing fallback for this turn.")
            self.mock_mode = True
            return self.listen_and_transcribe()
        except Exception as e:
            print(f"[Microphone Error] General failure: {e}")
            print("Switching to manual typing fallback for this turn.")
            self.mock_mode = True
            return self.listen_and_transcribe()
