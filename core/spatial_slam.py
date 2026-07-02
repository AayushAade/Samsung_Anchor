import cv2
import numpy as np
import time

class MemoraSpatialSLAM:
    """
    Visual SLAM & Scene/Room classifier (Pillar II).
    Uses frame color signature matching for visual room classification,
    and supports simulated BLE beacon transitions with hysteresis.
    """
    def __init__(self, mock_mode=False):
        self.mock_mode = mock_mode
        self.registered_rooms = {}  # room_name -> visual signature (mean HSV values)
        self.current_room = "Living Room"
        self.last_transition_time = time.time()
        self.mock_rooms = ["Living Room", "Kitchen", "Bedroom", "Bathroom"]
        self.mock_index = 0

    def register_room(self, room_name, frame):
        """
        Registers a room with its visual signature (average color in HSV space).
        """
        if frame is None:
            return False
        
        try:
            # Convert to HSV to be slightly more robust to lighting changes
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mean_color = hsv.mean(axis=(0, 1)) # [H, S, V] average
            self.registered_rooms[room_name] = mean_color
            print(f"[Spatial SLAM] Registered room '{room_name}' with visual signature {mean_color}")
            return True
        except Exception as e:
            print(f"[Spatial SLAM Error] Failed to register room {room_name}: {e}")
            return False

    def classify_room(self, frame):
        """
        Classifies the current frame into one of the registered rooms.
        If mock_mode is enabled or no rooms are registered, it simulates BLE-based room transitions.
        """
        if self.mock_mode or not self.registered_rooms:
            # Simulate a room transition every 15 seconds to mimic walking through a house
            now = time.time()
            if now - self.last_transition_time > 15:
                self.mock_index = (self.mock_index + 1) % len(self.mock_rooms)
                self.current_room = self.mock_rooms[self.mock_index]
                self.last_transition_time = now
                print(f"[Spatial SLAM Sim] Room transition detected! Now in: {self.current_room}")
            return self.current_room

        # Visual Room Classification using Euclidean distance of average HSV color
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            current_sig = hsv.mean(axis=(0, 1))
            
            best_room = self.current_room
            min_dist = float("inf")
            
            for room_name, signature in self.registered_rooms.items():
                dist = np.linalg.norm(current_sig - signature)
                if dist < min_dist:
                    min_dist = dist
                    best_room = room_name
            
            # Apply a hysteresis threshold to avoid rapid room flickering
            # Only transition if distance difference is substantial, or keep current
            if best_room != self.current_room:
                # Calculate distance to current room signature
                current_sig_ref = self.registered_rooms.get(self.current_room)
                if current_sig_ref is not None:
                    current_dist = np.linalg.norm(current_sig - current_sig_ref)
                    # Hysteresis threshold
                    if current_dist - min_dist > 15.0:
                        self.current_room = best_room
                        print(f"[Spatial SLAM] Visual transition detected! Entered: {self.current_room}")
                else:
                    self.current_room = best_room
            
        except Exception as e:
            print(f"[Spatial SLAM Error] Visual classification failed: {e}")
            
        return self.current_room

    def force_room_transition(self, room_name):
        """Manually forces a room transition (simulating a BLE beacon trigger)."""
        self.current_room = room_name
        self.last_transition_time = time.time()
        print(f"[Spatial SLAM] Room transition forced. Room set to: {self.current_room}")
        return True
