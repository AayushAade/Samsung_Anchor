import argparse
import cv2
import sys
import time
import os

from config import settings
from core.database import MemoraDatabase
from core.face_recognizer import MemoraFaceRecognizer
from core.audio_listener import MemoraAudioListener
from core.context_binder import MemoraContextBinder

def parse_args():
    parser = argparse.ArgumentParser(description="Memora Week 1 MVP: Unsupervised Identity Binding")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without physical camera/mic")
    parser.add_argument("--tolerance", type=float, default=settings.FACE_TOLERANCE, help="Face comparison tolerance (lower is stricter)")
    parser.add_argument("--db", type=str, default=settings.DB_PATH, help="Path to database JSON file")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("=" * 60)
    print("🧠 MEMORA: The Autonomous External Hippocampus")
    print("🎯 Week 1 MVP: Unsupervised Identity Binding")
    print("=" * 60)

    # Initialize components
    db = MemoraDatabase(args.db)
    recognizer = MemoraFaceRecognizer(tolerance=args.tolerance, mock_mode=args.mock)
    
    # Initialize audio listener
    listener = MemoraAudioListener(duration_sec=settings.AUDIO_DURATION_SEC, mock_mode=args.mock)
    
    # Initialize LLM context binder
    binder = MemoraContextBinder()

    # Determine if we run in mock mode
    mock_mode = args.mock or recognizer.mock_mode
    if mock_mode:
        print("[System Info] Running in SIMULATED (mock) mode.")
    else:
        print("[System Info] Running in REAL mode using camera and microphone.")

    # Try to open the webcam
    cap = None
    if not mock_mode:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[Camera Warning] Could not open physical webcam. Falling back to Simulated Mode.")
            mock_mode = True
            recognizer.mock_mode = True
            listener.mock_mode = True

    # Face binding state
    # We keep track of faces we've already tried to listen to in this session
    # to avoid repeating the audio prompt constantly for the same face.
    attempted_bindings = set()

    try:
        if mock_mode:
            # Simulated Webcam/Loop
            print("\nStarting Simulated loop. Press Ctrl+C to exit.")
            
            # Create a blank black frame for display
            sim_frame = bytes() # placeholder
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
                    is_new = res["is_new"]

                    if is_new:
                        print(f"\n[Camera] {face_id} detected.")
                        
                    # If the face has no name yet and we haven't asked this session
                    if not name and face_id not in attempted_bindings:
                        attempted_bindings.add(face_id)
                        print(f"\n[System] Activating ambient audio context listener for {face_id}...")
                        
                        # Listen for audio context
                        transcript = listener.listen_and_transcribe()
                        
                        if transcript:
                            print(f"[System] LLM Parsing transcript...")
                            binding_info = binder.parse_transcript(transcript)
                            extracted_name = binding_info.get("extracted_name")
                            relationship = binding_info.get("relationship")
                            
                            if extracted_name:
                                db.bind_name(face_id, extracted_name, relationship)
                                rel_str = f" ({relationship})" if relationship else ""
                                print(f"\n>>> Identity Confirmed: {extracted_name}{rel_str} <<<")
                            else:
                                print(f"[System] No name identified in conversation context for {face_id}.")
                        else:
                            print(f"[System] No audio context captured.")

                # Check for exit key
                if cv2.waitKey(30) & 0xFF == ord('q'):
                    break
                
                # Slow down the simulation loop
                time.sleep(1)

        else:
            # Real Webcam Loop
            print("\nWebcam started. Stand in front of the camera. Press 'q' in the window to quit.")
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("[Camera Error] Failed to grab frame.")
                    break

                # Process the frame to get face results
                results = recognizer.process_frame(frame, db)
                recognizer.draw_faces(frame, results)

                # Show the image
                cv2.imshow("Memora AR Wearable Hub (Week 1)", frame)

                # Check results
                for res in results:
                    face_id = res["face_id"]
                    name = res["name"]
                    is_new = res["is_new"]

                    if is_new:
                        print(f"\n[Camera] {face_id} detected.")

                    # If the face has no name and we haven't attempted to listen to them yet in this session
                    if not name and face_id not in attempted_bindings:
                        attempted_bindings.add(face_id)
                        print(f"\n[System] Activating ambient audio context listener for {face_id}...")
                        
                        # Pause camera frame processing momentarily for audio capture
                        transcript = listener.listen_and_transcribe()
                        
                        if transcript:
                            print(f"[System] LLM Parsing transcript...")
                            binding_info = binder.parse_transcript(transcript)
                            extracted_name = binding_info.get("extracted_name")
                            relationship = binding_info.get("relationship")
                            
                            if extracted_name:
                                db.bind_name(face_id, extracted_name, relationship)
                                rel_str = f" ({relationship})" if relationship else ""
                                print(f"\n>>> Identity Confirmed: {extracted_name}{rel_str} <<<")
                            else:
                                print(f"[System] No name identified in conversation context for {face_id}.")
                        else:
                            print(f"[System] No audio context captured.")

                # Check for exit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    except KeyboardInterrupt:
        print("\n[System Info] Program interrupted by user.")
    finally:
        # Cleanup
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        print("\nDemo finished. Database state saved.")

if __name__ == "__main__":
    # Ensure numpy is imported for mock mode
    import numpy as np
    main()
