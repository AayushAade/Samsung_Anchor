import argparse
import cv2
import sys
import time
import os
from datetime import datetime
import numpy as np

from config import settings
from core.database import MemoraDatabase
from core.spatial_slam import MemoraSpatialSLAM
from core.object_ledger import MemoraObjectTracker
from core.audio_listener import MemoraAudioListener
from core.context_binder import MemoraContextBinder
from core.speaker import MemoraSpeaker

def parse_args():
    parser = argparse.ArgumentParser(description="Memora Week 2 MVP: The Visual Ledger")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without physical camera/mic")
    parser.add_argument("--db", type=str, default=settings.DB_PATH, help="Path to database JSON file")
    return parser.parse_args()

def get_time_elapsed_string(iso_timestamp):
    """Calculates human-readable time elapsed since the given ISO timestamp."""
    try:
        seen_time = datetime.fromisoformat(iso_timestamp)
        elapsed_sec = (datetime.now() - seen_time).total_seconds()
        
        if elapsed_sec < 0:
            return "just now"
        if elapsed_sec < 60:
            return "just now"
        
        minutes = int(elapsed_sec // 60)
        if minutes < 60:
            return f"1 minute ago" if minutes == 1 else f"{minutes} minutes ago"
        
        hours = int(minutes // 60)
        return f"1 hour ago" if hours == 1 else f"{hours} hours ago"
    except Exception:
        return "recently"

def main():
    args = parse_args()
    
    print("=" * 60)
    print("🧠 MEMORA: The Autonomous External Hippocampus")
    print("🔍 Week 2 MVP: Passive Object Tracking & The Visual Ledger")
    print("=" * 60)

    # Initialize components
    db = MemoraDatabase(args.db)
    tracker = MemoraObjectTracker(mock_mode=args.mock)
    slam = MemoraSpatialSLAM(mock_mode=args.mock)
    listener = MemoraAudioListener(duration_sec=4, mock_mode=args.mock)
    binder = MemoraContextBinder()
    speaker = MemoraSpeaker()

    # Determine if running in mock mode
    mock_mode = args.mock or tracker.mock_mode
    if mock_mode:
        print("[System Info] Running in SIMULATED (mock) mode.")
    else:
        print("[System Info] Running in REAL mode using camera.")

    # Try to open the webcam
    cap = None
    if not mock_mode:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[Camera Warning] Could not open physical webcam. Falling back to Simulated Mode.")
            mock_mode = True
            tracker.mock_mode = True
            slam.mock_mode = True
            listener.mock_mode = True

    # Active query prompt state
    active_whisper = None
    whisper_display_until = 0

    # For simulated room cycling in mock mode
    room_options = ["Living Room", "Kitchen", "Bedroom", "Bathroom"]
    current_room_idx = 0
    slam.force_room_transition(room_options[current_room_idx])

    print("\n" + "*" * 50)
    print("CONTROLS:")
    print("  Press 'f' - Trigger Voice Search (Ask 'Where is my phone?')")
    print("  Press 'r' - Manually cycle Rooms (simulating BLE Beacon transitions)")
    print("  Press 'q' - Exit Program")
    print("*" * 50 + "\n")

    try:
        while True:
            # 1. Grab Frame
            if mock_mode:
                # Generate a dummy frame for display
                frame = 120 * np.ones((480, 640, 3), dtype=np.uint8)
                
                # Add background grid layout representation
                cv2.rectangle(frame, (10, 10), (630, 470), (40, 40, 40), 1)
                
                # Draw mock visual room cues
                current_room = db.get_current_room()
                if current_room == "Living Room":
                    # Draw a sofa
                    cv2.rectangle(frame, (150, 350), (490, 420), (100, 70, 50), -1)
                elif current_room == "Kitchen":
                    # Draw a counter table
                    cv2.rectangle(frame, (50, 380), (590, 450), (150, 150, 150), -1)
                elif current_room == "Bedroom":
                    # Draw a bed
                    cv2.rectangle(frame, (100, 320), (350, 420), (80, 80, 120), -1)
                else:
                    # Bathroom sink area
                    cv2.rectangle(frame, (200, 340), (440, 430), (180, 180, 180), -1)
                    cv2.circle(frame, (320, 360), 20, (230, 230, 250), -1)

                cv2.putText(frame, "MEMORA AR SMARTGLASS SIMULATOR", (120, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            else:
                ret, frame = cap.read()
                if not ret:
                    print("[Camera Error] Failed to grab frame.")
                    break

            # 2. Run Room Classifier & Sync with Database
            current_room = slam.classify_room(frame)
            db.set_current_room(current_room)

            # 3. Detect Objects
            detections = tracker.detect_objects(frame)

            # 4. Log Objects into Spatial Database Ledger
            for det in detections:
                name = det["name"]
                cx, cy = det["center"]
                box = det["box"]
                db.log_object(name, cx, cy, current_room, box)

            # 5. Draw HUD and Spatial Mapping Overlay
            tracker.draw_ledger_overlay(frame, detections)

            # Draw Room Tag Overlay
            cv2.rectangle(frame, (10, 70), (250, 115), (0, 0, 0), cv2.FILLED)
            cv2.rectangle(frame, (10, 70), (250, 115), (0, 255, 255), 1)
            cv2.putText(frame, f"ZONE: {current_room}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            total_items = len(db.data.get("objects", {}))
            cv2.putText(frame, f"TRACKED ITEMS IN LEDGER: {total_items}", (20, 107), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

            # Draw "Proactive Whisper" box if active
            if active_whisper and time.time() < whisper_display_until:
                # Wrap text lines
                h_pos = 140
                cv2.rectangle(frame, (10, 420), (630, 465), (0, 50, 0), cv2.FILLED)
                cv2.rectangle(frame, (10, 420), (630, 465), (0, 255, 0), 2)
                cv2.putText(frame, "🔊 MEMORA WHISPER:", (20, 437), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
                cv2.putText(frame, f'"{active_whisper}"', (20, 455), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            else:
                active_whisper = None

            # Render key controls overlay at bottom right
            cv2.putText(frame, "Press 'f': Query  'r': Transition  'q': Exit", (330, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

            # Show Frame
            cv2.imshow("Memora Visual Ledger Hub (Week 2)", frame)

            # Handle keyboard triggers
            key = cv2.waitKey(30) & 0xFF
            
            # 'f' key: Find/Query object location
            if key == ord('f'):
                print("\n[System] Activating Query Listener...")
                # Stop updating UI for a second to listen
                query_text = listener.listen_and_transcribe()
                
                if query_text:
                    print(f"[System] LLM Parsing Query: \"{query_text}\"")
                    query_info = binder.parse_location_query(query_text)
                    target = query_info.get("target_object")
                    
                    if target:
                        # Search for matching object in database keys
                        matched_db_key = None
                        target_lower = target.lower()
                        
                        # Match name intelligently
                        for obj_name in db.data.get("objects", {}).keys():
                            if target_lower in obj_name.lower() or obj_name.lower() in target_lower:
                                matched_db_key = obj_name
                                break
                                
                        if matched_db_key:
                            info = db.get_last_known_location(matched_db_key)
                            cx, cy = info["x"], info["y"]
                            quadrant = tracker.spatial_hash.get_grid_quadrant(cx, cy)
                            time_str = get_time_elapsed_string(info["last_seen"])
                            
                            active_whisper = f"Your {matched_db_key} was last seen in the {info['room']} ({quadrant}) {time_str}."
                            print(f"\n💬 MEMORA WHISPER: \"{active_whisper}\"\n")
                            speaker.speak(active_whisper)
                        else:
                            active_whisper = f"I haven't seen your {target} yet. Try scanning your surroundings."
                            print(f"\n💬 MEMORA WHISPER: \"{active_whisper}\"\n")
                            speaker.speak(active_whisper)
                    else:
                        active_whisper = "I couldn't identify the object you are searching for. Please ask clearly."
                        print(f"\n💬 MEMORA WHISPER: \"{active_whisper}\"\n")
                        speaker.speak(active_whisper)
                    
                    whisper_display_until = time.time() + 8.0 # Display overlay for 8 seconds
                else:
                    print("[System] No query captured.")

            # 'r' key: Simulate room transitions manually
            elif key == ord('r'):
                current_room_idx = (current_room_idx + 1) % len(room_options)
                slam.force_room_transition(room_options[current_room_idx])
                
            # 'q' key: Quit
            elif key == ord('q'):
                break
                
            if mock_mode:
                # Slow down mock CPU usage
                time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n[System Info] Program interrupted by user.")
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        print("\nDemo finished. Database state saved.")

if __name__ == "__main__":
    main()
