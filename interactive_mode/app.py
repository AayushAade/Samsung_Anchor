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
from core.speaker import MemoraSpeaker
from core.event_logger import log_event

def parse_args():
    parser = argparse.ArgumentParser(description="Memora Interactive Mode: Manual Anchoring & Querying")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without physical camera")
    parser.add_argument("--tolerance", type=float, default=settings.FACE_TOLERANCE, help="Face comparison tolerance")
    parser.add_argument("--db", type=str, default=settings.DB_PATH, help="Path to database SQLite file")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print("=" * 60)
    print("🧠 MEMORA INTERACTIVE MODE: Manual Anchoring & Querying")
    print("=" * 60)
    print("[Instructions]")
    print("  - If an anonymous face is on screen, press 'r' to register.")
    print("  - If a registered face is on screen, press 'd' to announce.")
    print("  - Press 'q' to quit.")
    print("=" * 60)

    # Initialize modules
    db = MemoraDatabase(args.db)
    recognizer = MemoraFaceRecognizer(tolerance=args.tolerance, mock_mode=args.mock)
    speaker = MemoraSpeaker()

    mock_mode = args.mock or recognizer.mock_mode
    cap = None
    if not mock_mode:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[Camera Warning] Could not open physical webcam. Falling back to Mock Mode.")
            mock_mode = True
            recognizer.mock_mode = True

    try:
        while True:
            # 1. Grab Frame
            if mock_mode:
                frame = 128 * np.ones((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, "MEMORA INTERACTIVE SIMULATOR", (110, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, "Press 'r' to register / 'd' to announce", (130, 420), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Draw mock person representation
                cv2.circle(frame, (320, 240), 80, (200, 200, 200), -1)
                cv2.rectangle(frame, (240, 320), (400, 480), (150, 150, 150), -1)
            else:
                ret, frame = cap.read()
                if not ret:
                    print("[Camera Error] Failed to grab frame.")
                    break

            # 2. Process frame with persistent tracking
            results = recognizer.process_frame(frame, db)
            
            # 3. Custom bounding box drawings for interactive mode
            for res in results:
                top, right, bottom, left = res["box"]
                face_id = res["face_id"]
                name = res["name"]
                relationship = res["relationship"]
                label_override = res.get("label")

                # Override drawings to indicate interactive options
                if name:
                    color = (0, 255, 0) # Green
                    rel_str = f" ({relationship})" if relationship else ""
                    label = f"{name}{rel_str} | [d] Announce"
                elif label_override:
                    color = (0, 165, 255) # Orange (stabilizing candidate)
                    label = label_override
                else:
                    color = (0, 0, 255) # Red (anonymous)
                    label = f"{face_id} | [r] Register"

                # Draw bounding box and filled label background
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, label, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow("Memora Interactive Mode", frame)

            # 4. Handle Keypresses
            key = cv2.waitKey(100) & 0xFF
            if key == ord('q'):
                break

            elif key == ord('r'):
                # Registration triggered: find first anonymous face currently visible
                anon_res = [r for r in results if r["face_id"] is not None and r["name"] is None]
                if anon_res:
                    target_face = anon_res[0]
                    target_id = target_face["face_id"]
                    
                    print(f"\n[Register Triggered] Found face: {target_id}")
                    # Prompt the user on the console
                    choice = input("Do you want to register this person? (y/n): ").strip().lower()
                    if choice == 'y':
                        name = input("Enter Name: ").strip()
                        relationship = input("Enter Relationship: ").strip()
                        
                        if name:
                            db.bind_name(target_id, name, relationship if relationship else None)
                            log_event("confirmed", f"Registered [{name}] as your [{relationship if relationship else 'None'}]")
                            confirm_text = f"Registered {name} as your {relationship if relationship else 'acquaintance'}."
                            speaker.speak(confirm_text)
                        else:
                            print("[System] Name cannot be empty. Registration aborted.")
                    else:
                        print("[System] Registration skipped.")
                else:
                    print("\n[System Warning] No anonymous faces visible to register.")

            elif key == ord('d'):
                # Announcement query triggered: find first registered face currently visible
                reg_res = [r for r in results if r["face_id"] is not None and r["name"] is not None]
                if reg_res:
                    target_face = reg_res[0]
                    target_name = target_face["name"]
                    target_rel = target_face["relationship"]
                    
                    rel_phrase = f". She/He is your {target_rel}" if target_rel else ""
                    announce_text = f"{target_name} is here{rel_phrase}."
                    
                    log_event("speaker", f"Speaker announcement: \"{announce_text}\"")
                    speaker.speak(announce_text)
                else:
                    print("\n[System Warning] No registered faces visible to announce.")

    except KeyboardInterrupt:
        print("\n[System Info] Interactive mode terminated by user.")
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        print("\nInteractive mode closed. Database saved.")

if __name__ == "__main__":
    main()
