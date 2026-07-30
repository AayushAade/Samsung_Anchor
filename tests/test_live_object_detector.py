import pytest
import numpy as np
import cv2
from src.perception.object_detector import ObjectDetector
from src.perception.sensor_models import DetectedObject, RoomLocation
from src.perception.perception_manager import PerceptionManager


def test_live_object_detector_accepts_raw_opencv_frame():
    detector = ObjectDetector(mode="LIVE")

    # Create synthetic OpenCV BGR frame containing a rectangular object (e.g. Reading Glasses shape)
    raw_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(raw_frame, (300, 200), (500, 270), (255, 255, 255), -1)

    objects = detector.detect_objects_from_frame(raw_frame, RoomLocation.LIVING_ROOM, frame_id=42)

    assert isinstance(objects, list)
    assert len(objects) >= 1
    obj = objects[0]
    assert isinstance(obj, DetectedObject)
    assert obj.object_name in ["Reading Glasses", "Water Bottle", "Medication Bottle", "Walking Cane", "Television Remote"]
    assert obj.confidence > 0.80
    assert obj.bounding_box is not None
    assert len(obj.bounding_box) == 4
    assert obj.frame_id == 42


def test_live_object_detector_empty_scene_returns_no_detections():
    detector = ObjectDetector(mode="LIVE")

    # Completely black frame with no visible objects
    black_frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    objects = detector.detect_objects_from_frame(black_frame, RoomLocation.LIVING_ROOM, frame_id=101)

    assert isinstance(objects, list)
    assert len(objects) == 0  # No hallucinated detections on empty scenes


def test_simulation_fallback_when_raw_frame_is_none():
    detector = ObjectDetector(mode="AUTO")

    # raw_frame is None -> Should gracefully trigger SIMULATION DETECTOR fallback
    objects = detector.detect_objects_for_room(RoomLocation.LIVING_ROOM, raw_frame=None)

    assert isinstance(objects, list)
    assert len(objects) >= 1
    assert any(o.object_name == "Reading Glasses" for o in objects)


def test_developer_debug_visualization_mode():
    detector = ObjectDetector(mode="LIVE")

    raw_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    cv2.rectangle(raw_frame, (100, 100), (250, 350), (255, 255, 255), -1)

    objects = detector.detect_objects_from_frame(raw_frame, RoomLocation.LIVING_ROOM, frame_id=1)
    annotated = detector.draw_detections(raw_frame, objects)

    assert annotated is not None
    assert annotated.shape == raw_frame.shape


def test_perception_manager_integration_live_object_detection():
    pm = PerceptionManager()

    # Process perception cycle
    context = pm.process_cycle()

    assert context is not None
    assert isinstance(context.detected_objects, list)
