import argparse
import cv2
import sys
import time
import os
import numpy as np
import threading

from config import settings
from core.database import MemoraDatabase
from core.face_recognizer import MemoraFaceRecognizer
from core.audio_listener import MemoraAudioListener
from core.context_binder import MemoraContextBinder
from core.speaker import MemoraSpeaker
from core.event_logger import log_event

# Global background listening states
is_listening = False
active_listening_face = None
listening_lock = threading.Lock()
last_listen_time = {}  # face_id -> timestamp when last listening finished

def parse_args():
    parser = argparse.ArgumentParser(description="Memora Week 1 MVP: Unsupervised Identity Binding")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without physical camera/mic")
    parser.add_argument("--tolerance", type=float, default=settings.FACE_TOLERANCE, help="Face comparison tolerance (lower is stricter)")
    parser.add_argument("--db", type=str, default=settings.DB_PATH, help="Path to database SQLite file")
    parser.add_argument("--mic-index", type=int, default=None, help="Explicit microphone device index to use")
    return parser.parse_args()

def handle_async_listening(face_id, db, listener, binder, speaker):
    """
    Spawns a background thread to listen to the microphone and process the transcript,
    keeping the camera feed completely smooth in the main thread.
    """
    global is_listening, active_listening_face
    
    with listening_lock:
        is_listening = True
        active_listening_face = face_id

    def run_bg_listen():
        global is_listening, active_listening_face, last_listen_time
        try:
            transcript = listener.listen_and_transcribe()
            
            if transcript:
                if settings.DEBUG:
                    print(f"[System] LLM Parsing transcript...")
                binding_info = binder.parse_transcript(transcript)
                extracted_name = binding_info.get("extracted_name")
                relationship = binding_info.get("relationship")
                
                if extracted_name:
                    ev_res = db.add_evidence(face_id, extracted_name, relationship, raw_transcript=transcript)
                    conf = int(ev_res["confidence"] * 100)
                    log_event("evidence", f"Evidence added for [{face_id}]: candidate '{ev_res['name']}' (relationship: '{ev_res['relationship']}') with confidence {conf}%")
                    
                    if ev_res["is_confirmed"]:
                        rel_str = f" ({ev_res['relationship']})" if ev_res['relationship'] else ""
                        log_event("confirmed", f"[{ev_res['name']}] identity confirmed (Confidence: {conf}%)")
                        log_event("speaker", f"Speaker announcement: \"Identity confirmed. This is {ev_res['name']}.\"")
                        speaker.speak(f"Identity confirmed. This is {ev_res['name']}.")
                    else:
                        if settings.DEBUG:
                            print(f"[System] Confidence ({conf}%) is below confirmation threshold (80%). Logged for caregiver confirmation.")
                else:
                    if settings.DEBUG:
                        print(f"[System] No name identified in conversation context for {face_id}.")
            else:
                if settings.DEBUG:
                    print(f"[System] No audio context captured.")
        finally:
            # Update last listen timestamp and release lock
            last_listen_time[face_id] = time.time()
            with listening_lock:
                is_listening = False
                active_listening_face = None

    threading.Thread(target=run_bg_listen, daemon=True).start()

def main():
    global is_listening, active_listening_face
    args = parse_args()
    
    print("=" * 60)
    print("🧠 MEMORA: The Autonomous External Hippocampus")
    print("🎯 Week 1 MVP: Unsupervised Identity Binding")
    print("=" * 60)

    # Initialize components
    db = MemoraDatabase(args.db)
    recognizer = MemoraFaceRecognizer(tolerance=args.tolerance, mock_mode=args.mock)
    
    # Initialize audio listener with potential mic index override
    listener = MemoraAudioListener(duration_sec=settings.AUDIO_DURATION_SEC, mock_mode=args.mock, device_index=args.mic_index)
    
    # Initialize LLM context binder
    binder = MemoraContextBinder()
    
    # Initialize speaker output
    speaker = MemoraSpeaker()

    # Determine if we run in mock mode
    mock_mode = args.mock or recognizer.mock_mode
    if mock_mode:
        print("[System Info] Running in SIMULATED (mock) mode.")
    else:
        print("[System Info] Running in REAL mode using camera and microphone.")
        print("[Instructions] Press 't' in the camera window to force manual typing input.")
        print("[Instructions] Press 'q' in the camera window to quit.")

    # Try to open the webcam
    cap = None
    if not mock_mode:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[Camera Warning] Could not open physical webcam. Falling back to Simulated Mode.")
            mock_mode = True
            recognizer.mock_mode = True
            listener.mock_mode = True

    # Face announcement state
    announced_identities = set()

    try:
        if mock_mode:
            print("\nStarting Simulated loop. Press Ctrl+C to exit.")
            
            while True:
                # Generate a dummy frame for cv2 to show
                frame = 128 * np.ones((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "MEMORA SIMULATOR", (180, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                cv2.putText(frame, "Webcam Simulated Frame", (200, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Draw a representation of a person
                cv2.circle(frame, (320, 240), 80, (200, 200, 200), -1) # Head
                cv2.rectangle(frame, (240, 320), (400, 480), (150, 150, 150), -1) # Shoulders

                # Process this frame
                results = recognizer.process_frame(frame, db)
                recognizer.draw_faces(frame, results)

                # Display the simulated frame
                cv2.imshow("Memora AR Wearable Simulator", frame)
                
                for res in results:
                    face_id = res["face_id"]
                    name = res["name"]
                    relationship = res["relationship"]

                    if name:
                        # Greeting announcement if not yet done in this session
                        if face_id not in announced_identities:
                            announced_identities.add(face_id)
                            rel_phrase = f". She/He is your {relationship}" if relationship else ""
                            log_event("speaker", f"Speaker announcement: \"{name} is here{rel_phrase}.\"")
                            speaker.speak(f"{name} is here{rel_phrase}.")
                    elif face_id is not None:
                        # Check if we should trigger background listening
                        with listening_lock:
                            can_listen = not is_listening
                        
                        cooldown_expired = (face_id not in last_listen_time) or (time.time() - last_listen_time[face_id] > 5.0)
                        
                        if can_listen and cooldown_expired:
                            candidates = db.get_candidates(face_id)
                            if candidates and settings.DEBUG:
                                top_cand = candidates[0]
                                cand_name = top_cand["name"]
                                cand_conf = int(top_cand["confidence"] * 100)
                                cand_rel = f" ({top_cand['relationship']})" if top_cand["relationship"] else ""
                                print(f"[Caregiver Log] Candidate: {cand_name}{cand_rel} | Confidence: {cand_conf}%")
                            
                            handle_async_listening(face_id, db, listener, binder, speaker)

                # Check keys
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('t'):
                    print("\n[System] Manual override triggered. Switching to typing input fallback.")
                    listener.mock_mode = True
                
                time.sleep(0.1)

        else:
            print("\nWebcam started. Stand in front of the camera.")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[Camera Error] Failed to grab frame.")
                    break

                # Process the frame to get face results
                results = recognizer.process_frame(frame, db)
                recognizer.draw_faces(frame, results)

                # Show the image (refreshes continuously at 30fps)
                cv2.imshow("Memora AR Wearable Hub (Week 1)", frame)

                for res in results:
                    face_id = res["face_id"]
                    name = res["name"]
                    relationship = res["relationship"]

                    if name:
                        # Greeting announcement if not yet done in this session
                        if face_id not in announced_identities:
                            announced_identities.add(face_id)
                            rel_phrase = f". She/He is your {relationship}" if relationship else ""
                            log_event("speaker", f"Speaker announcement: \"{name} is here{rel_phrase}.\"")
                            speaker.speak(f"{name} is here{rel_phrase}.")
                    elif face_id is not None:
                        # Check if we should trigger background listening
                        with listening_lock:
                            can_listen = not is_listening
                        
                        cooldown_expired = (face_id not in last_listen_time) or (time.time() - last_listen_time[face_id] > 5.0)
                        
                        if can_listen and cooldown_expired:
                            candidates = db.get_candidates(face_id)
                            if candidates and settings.DEBUG:
                                top_cand = candidates[0]
                                cand_name = top_cand["name"]
                                cand_conf = int(top_cand["confidence"] * 100)
                                cand_rel = f" ({top_cand['relationship']})" if top_cand["relationship"] else ""
                                print(f"[Caregiver Log] Candidate: {cand_name}{cand_rel} | Confidence: {cand_conf}%")

                            handle_async_listening(face_id, db, listener, binder, speaker)

                # Check keys
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('t'):
                    print("\n[System] Manual override triggered. Switching to typing input fallback.")
                    listener.mock_mode = True

    except KeyboardInterrupt:
        print("\n[System Info] Program interrupted by user.")
    finally:
        # Cleanup
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        print("\nDemo finished. Database state saved.")

if __name__ == "__main__":
    main()
