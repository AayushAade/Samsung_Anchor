from src.perception.face_tracker import FaceTracker


def test_face_tracker_continuity():
    tracker = FaceTracker()
    rec1 = {"faces": [{"face_id": "F1", "name": "Sarah", "confidence": 0.9}]}
    faces1 = tracker.update_faces(rec1)

    assert len(faces1) == 1
    assert faces1[0].name == "Sarah"
    assert faces1[0].is_known is True

    # Unknown face
    rec2 = {"faces": [{"face_id": "F2", "name": "Unknown", "confidence": 0.8}]}
    faces2 = tracker.update_faces(rec2)

    assert len(tracker.get_tracked_faces()) == 2
