from datetime import datetime
from typing import List, Dict, Optional
from src.perception.sensor_models import DetectedFace


class FaceTracker:
    """
    Persistent face tracking maintaining visitor and family identity continuity.
    """

    def __init__(self) -> None:
        self._tracked_faces: Dict[str, DetectedFace] = {}

    def update_faces(self, recognition_result: dict) -> List[DetectedFace]:
        now_str = datetime.now().strftime("%H:%M:%S")
        faces_data = recognition_result.get("faces", [])

        current_active = []
        for face in faces_data:
            fid = face.get("face_id", "Face_Unknown")
            name = face.get("name")
            conf = face.get("confidence", 0.90)
            is_known = bool(name and name.lower() != "unknown")

            if fid in self._tracked_faces:
                tf = self._tracked_faces[fid]
                tf.last_seen = now_str
                tf.confidence = conf
                if name:
                    tf.name = name
                    tf.is_known = is_known
            else:
                tf = DetectedFace(
                    face_id=fid,
                    name=name,
                    confidence=conf,
                    first_seen=now_str,
                    last_seen=now_str,
                    is_known=is_known,
                )
                self._tracked_faces[fid] = tf

            current_active.append(tf)

        return current_active

    def get_tracked_faces(self) -> List[DetectedFace]:
        return list(self._tracked_faces.values())
