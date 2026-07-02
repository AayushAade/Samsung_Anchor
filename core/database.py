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
            "next_anon_index": 1   # Counter for generating Anonymous_ID_1, Anonymous_ID_2, etc.
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

    def clear(self):
        """Clears all database contents (useful for testing)."""
        with self.lock:
            self.data = {
                "identities": {},
                "next_anon_index": 1
            }
            self.save_unlocked()
