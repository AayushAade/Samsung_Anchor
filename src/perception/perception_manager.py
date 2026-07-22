from typing import Optional
from src.perception.activity_detector import ActivityDetector
from src.perception.audio_pipeline import AudioPipeline
from src.perception.camera_pipeline import CameraPipeline
from src.perception.face_tracker import FaceTracker
from src.perception.multimodal_fusion import MultimodalFusionEngine
from src.perception.object_detector import ObjectDetector
from src.perception.room_tracker import RoomTracker
from src.perception.sensor_models import AudioEventType, PerceptionContext, RoomLocation


class PerceptionManager:
    """
    Central orchestrator for the Edge Perception Layer.
    Executes real-time perception cycles and yields unified PerceptionContext.
    """

    def __init__(self) -> None:
        self.camera_pipeline = CameraPipeline()
        self.face_tracker = FaceTracker()
        self.object_detector = ObjectDetector()
        self.room_tracker = RoomTracker()
        self.activity_detector = ActivityDetector()
        self.audio_pipeline = AudioPipeline()
        self.fusion_engine = MultimodalFusionEngine()

    def process_cycle(self, recognition_result: Optional[dict] = None) -> PerceptionContext:
        rec = recognition_result or {}

        # 1. Acquire Frame Data
        frame = self.camera_pipeline.acquire_frame()

        # 2. Track Faces
        faces = self.face_tracker.update_faces(rec)

        # 3. Track Room & Objects
        room = self.room_tracker.get_current_room()
        objects = self.object_detector.detect_objects_for_room(room)

        # 4. Infer Activity
        obj_names = [o.object_name for o in objects]
        activity = self.activity_detector.infer_activity(room, obj_names, bool(faces))

        # 5. Audio Events
        audio_events = self.audio_pipeline.get_recent_audio_events()
        if not audio_events:
            self.audio_pipeline.detect_event(AudioEventType.SPEECH_PRESENT if faces else AudioEventType.SILENCE)
            audio_events = self.audio_pipeline.get_recent_audio_events()

        # 6. Fuse Multimodal Perception
        return self.fusion_engine.fuse(
            room=room,
            activity=activity,
            faces=faces,
            objects=objects,
            audio_events=audio_events,
            fps=frame.fps,
        )

    def set_room(self, room: RoomLocation) -> None:
        self.room_tracker.set_room(room)

    def trigger_audio_event(self, event_type: AudioEventType) -> None:
        self.audio_pipeline.detect_event(event_type)
