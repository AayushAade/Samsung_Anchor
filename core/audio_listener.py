import speech_recognition as sr
import sys

class MemoraAudioListener:
    def __init__(self, duration_sec=5, mock_mode=False):
        self.duration_sec = duration_sec
        self.mock_mode = mock_mode
        self.recognizer = sr.Recognizer()
        
        # Test if microphone is accessible, otherwise enable mock mode
        if not self.mock_mode:
            try:
                # Get a list of microphones
                mics = sr.Microphone.list_microphone_names()
                if not mics:
                    print("[Audio Listener Warning] No microphones found. Enabling typing fallback mode.")
                    self.mock_mode = True
            except Exception as e:
                print(f"[Audio Listener Warning] Microphone check failed: {e}. Enabling typing fallback mode.")
                self.mock_mode = True

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
            with sr.Microphone() as source:
                print(f"\n[Microphone] Adjusting for ambient noise... (1 second)")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print(f"[Microphone] Listening for {self.duration_sec} seconds... Speak now!")
                # Listen with timeout and duration limits
                audio = self.recognizer.listen(source, timeout=self.duration_sec + 2, phrase_time_limit=self.duration_sec)
                
                print("[Microphone] Processing audio...")
                # Recognize speech using Google Speech Recognition
                transcription = self.recognizer.recognize_google(audio)
                print(f"[Microphone] Transcribed: \"{transcription}\"")
                return transcription

        except sr.WaitTimeoutError:
            print("[Microphone Warning] No speech detected (timeout).")
            return None
        except sr.UnknownValueError:
            print("[Microphone Warning] Speech was detected but could not be understood.")
            return None
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
