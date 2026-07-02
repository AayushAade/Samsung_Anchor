import json
import os
import threading
from datetime import datetime
import numpy as np

# Import app settings
from config import settings

class MemoraDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or settings.DB_PATH
        self.lock = threading.Lock()
        self.data = {
            "identities": {},      # Map of face_id -> { "name": str/None, "relationship": str/None, "embeddings": [[float]*128], "created_at": str, "updated_at": str }
            "next_anon_index": 1,  # Counter for generating Anonymous_ID_1, Anonymous_ID_2, etc.
            "objects": {},         # Map of object_name -> { "last_seen": str, "x": float, "y": float, "room": str, "bounding_box": list, "history": list }
            "current_room": "Living Room"
        }
        self.load()

    def load(self):
        """Loads data from the JSON file database."""
        with self.lock:
            if os.path.exists(self.db_path):
                try:
                    with open(self.db_path, "r", encoding="utf-8") as f:
                        loaded_data = json.load(f)
                        # Ensure basic keys exist
                        if "identities" in loaded_data:
                            self.data["identities"] = loaded_data["identities"]
                        if "next_anon_index" in loaded_data:
                            self.data["next_anon_index"] = loaded_data["next_anon_index"]
                        if "objects" in loaded_data:
                            self.data["objects"] = loaded_data["objects"]
                        else:
                            self.data["objects"] = {}
                        if "current_room" in loaded_data:
                            self.data["current_room"] = loaded_data["current_room"]
                        else:
                            self.data["current_room"] = "Living Room"
                except Exception as e:
                    print(f"[Database Error] Failed to load database: {e}. Starting with empty database.")
            else:
                self.save_unlocked()

    def save(self):
        """Thread-safe save to file."""
        with self.lock:
            self.save_unlocked()

    def save_unlocked(self):
        """Saves data without acquiring lock (internal use)."""
        try:
            # Make sure parent directory exists
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"[Database Error] Failed to save database: {e}")

    def find_match(self, query_embedding, tolerance=None):
        """
        Compares query_embedding (128D list/array) against all stored identities.
        Returns (face_id, identity_dict, distance) if a match is found under the tolerance,
        otherwise returns (None, None, None).
        """
        if tolerance is None:
            tolerance = settings.FACE_TOLERANCE

        query_vector = np.array(query_embedding)
        best_match_id = None
        best_distance = float("inf")

        with self.lock:
            for face_id, info in self.data["identities"].items():
                for stored_embedding in info["embeddings"]:
                    stored_vector = np.array(stored_embedding)
                    # Compute Euclidean distance
                    distance = np.linalg.norm(query_vector - stored_vector)
                    if distance < tolerance and distance < best_distance:
                        best_distance = distance
                        best_match_id = face_id

            if best_match_id is not None:
                return best_match_id, self.data["identities"][best_match_id], best_distance

        return None, None, None

    def register_anonymous(self, embedding):
        """
        Registers a new anonymous identity with the given embedding vector.
        Returns the generated face_id.
        """
        with self.lock:
            anon_id = f"Anonymous_ID_{self.data['next_anon_index']}"
            self.data["next_anon_index"] += 1
            
            now_str = datetime.now().isoformat()
            self.data["identities"][anon_id] = {
                "name": None,
                "relationship": None,
                "embeddings": [list(embedding)],
                "created_at": now_str,
                "updated_at": now_str
            }
            self.save_unlocked()
            return anon_id

    def add_embedding_to_identity(self, face_id, embedding):
        """Adds a new embedding vector to an existing identity's database profile (for model reinforcement)."""
        with self.lock:
            if face_id in self.data["identities"]:
                self.data["identities"][face_id]["embeddings"].append(list(embedding))
                self.data["identities"][face_id]["updated_at"] = datetime.now().isoformat()
                self.save_unlocked()
                return True
        return False

    def bind_name(self, face_id, name, relationship=None):
        """
        Binds a name and optional relationship to an existing anonymous or known face_id.
        """
        with self.lock:
            if face_id in self.data["identities"]:
                self.data["identities"][face_id]["name"] = name
                if relationship:
                    self.data["identities"][face_id]["relationship"] = relationship
                self.data["identities"][face_id]["updated_at"] = datetime.now().isoformat()
                
                # If it's a confirmed name, we can also choose to rename the face_id key itself,
                # but to maintain stable references, we keep the original face_id key and update its metadata.
                self.save_unlocked()
                return True
        return False

    def get_identity(self, face_id):
        """Retrieves identity information for a given face_id."""
        with self.lock:
            return self.data["identities"].get(face_id)

    def get_all_identities(self):
        """Returns all identity records."""
        with self.lock:
            return dict(self.data["identities"])

    def log_object(self, object_name, x, y, room, bounding_box=None):
        """
        Logs the detection of an object with its coordinates, room, and optional bounding box.
        Updates the last known location and adds to the historical log.
        """
        with self.lock:
            now_str = datetime.now().isoformat()
            
            bbox_list = list(bounding_box) if bounding_box is not None else None
            entry = {
                "timestamp": now_str,
                "x": float(x),
                "y": float(y),
                "room": room,
                "bounding_box": bbox_list  # [x1, y1, x2, y2]
            }
            
            if object_name not in self.data["objects"]:
                self.data["objects"][object_name] = {
                    "last_seen": now_str,
                    "x": float(x),
                    "y": float(y),
                    "room": room,
                    "bounding_box": bbox_list,
                    "history": []
                }
            else:
                self.data["objects"][object_name]["last_seen"] = now_str
                self.data["objects"][object_name]["x"] = float(x)
                self.data["objects"][object_name]["y"] = float(y)
                self.data["objects"][object_name]["room"] = room
                self.data["objects"][object_name]["bounding_box"] = bbox_list
                
            # Limit history to last 50 sightings to save space
            self.data["objects"][object_name]["history"].append(entry)
            if len(self.data["objects"][object_name]["history"]) > 50:
                self.data["objects"][object_name]["history"].pop(0)
                
            self.save_unlocked()
            return True

    def get_last_known_location(self, object_name):
        """Retrieves the last known location of an object."""
        with self.lock:
            return self.data["objects"].get(object_name)

    def get_object_history(self, object_name):
        """Retrieves the history of detection events for an object."""
        with self.lock:
            if object_name in self.data["objects"]:
                return list(self.data["objects"][object_name]["history"])
            return []

    def set_current_room(self, room_name):
        """Sets the active room location of the device."""
        with self.lock:
            self.data["current_room"] = room_name
            self.save_unlocked()
            return True

    def get_current_room(self):
        """Gets the active room location of the device."""
        with self.lock:
            return self.data.get("current_room", "Living Room")

    def clear(self):
        """Clears all database contents (useful for testing)."""
        with self.lock:
            self.data = {
                "identities": {},
                "next_anon_index": 1,
                "objects": {},
                "current_room": "Living Room"
            }
            self.save_unlocked()
