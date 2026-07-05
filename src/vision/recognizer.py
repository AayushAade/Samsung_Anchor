import os
import json
import cv2
import numpy as np
import face_recognition
from typing import List, Dict, Any, Tuple, Union

class FaceRecognizer:
    """
    FaceRecognizer class responsible for taking a face crop, generating a 128D embedding,
    and comparing it against the known profiles database.
    """

    def __init__(self, db_path: str = None, threshold: float = 0.6):
        """
        Initializes the FaceRecognizer.

        Args:
            db_path: Path to the JSON database file. Defaults to known_profiles.json in the same folder.
            threshold: Euclidean distance threshold. Values below/equal to this are matches.
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "known_profiles.json")
        self.db_path = db_path
        self.threshold = threshold
        self.known_profiles: List[Dict[str, Any]] = []
        self.load_database()

    def load_database(self) -> None:
        """Loads profiles from the database file."""
        if not os.path.exists(self.db_path):
            self.known_profiles = []
            return
        try:
            with open(self.db_path, "r") as f:
                self.known_profiles = json.load(f)
        except Exception as e:
            # Silent fallback
            self.known_profiles = []

    def generate_embedding(self, face_crop: np.ndarray) -> Union[np.ndarray, None]:
        """
        Generates a 128-dimensional embedding from a cropped face image.

        Args:
            face_crop: OpenCV BGR image of the cropped face.

        Returns:
            A 128D numpy array embedding, or None if generation fails.
        """
        if face_crop is None or face_crop.size == 0:
            return None

        try:
            # Convert BGR (OpenCV) to RGB (face_recognition)
            rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
            h, w, _ = rgb_crop.shape

            # Generate encoding for the entire cropped image
            encodings = face_recognition.face_encodings(rgb_crop, known_face_locations=[(0, w, h, 0)])
            if encodings:
                return encodings[0]
        except Exception:
            pass
        return None

    def recognize(self, face_crop: np.ndarray) -> Tuple[str, float]:
        """
        Takes a face crop, generates an embedding, and finds the closest match in the database.

        Args:
            face_crop: OpenCV BGR image of the cropped face.

        Returns:
            A tuple of (Identity, Distance). Identity is 'Unknown' if no match is found.
        """
        embedding = self.generate_embedding(face_crop)
        if embedding is None:
            return "Unknown", 1.0

        # Reload database to capture any recent registrations
        self.load_database()

        if not self.known_profiles:
            return "Unknown", 1.0

        best_identity = "Unknown"
        min_distance = float("inf")

        for profile in self.known_profiles:
            db_emb = profile.get("embedding")
            if db_emb is None:
                continue
            db_emb_arr = np.array(db_emb)
            
            # Compute Euclidean distance
            distance = float(np.linalg.norm(embedding - db_emb_arr))
            if distance < min_distance:
                min_distance = distance
                if distance <= self.threshold:
                    best_identity = profile["name"]

        # If no profile was below the threshold, best_identity remains "Unknown"
        # but we return the minimum distance found (or 1.0 if not defined)
        if min_distance == float("inf"):
            min_distance = 1.0

        return best_identity, min_distance
