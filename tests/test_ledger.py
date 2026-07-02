import unittest
import numpy as np
import os
import time

from core.database import MemoraDatabase
from core.spatial_slam import MemoraSpatialSLAM
from core.object_ledger import SpatialHashMap, MemoraObjectTracker
from core.context_binder import MemoraContextBinder

class TestObjectLedgerAndSLAM(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test_ledger_db.json"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = MemoraDatabase(db_path=self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_spatial_hash_map(self):
        spatial_hash = SpatialHashMap(cell_size=100)
        
        # Test hashing
        cell_x, cell_y = spatial_hash.hash_point(150, 250)
        self.assertEqual(cell_x, 1)
        self.assertEqual(cell_y, 2)

        # Test insert and retrieve
        spatial_hash.insert("keys", 150, 250, {"confidence": 0.95})
        items = spatial_hash.get_items_in_cell(180, 220)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "keys")
        self.assertAlmostEqual(items[0]["coords"][0], 150.0)

        # Test grid quadrant description
        quadrant = spatial_hash.get_grid_quadrant(100, 100, width=640, height=480)
        self.assertEqual(quadrant, "top-left area")
        
        quadrant_center = spatial_hash.get_grid_quadrant(320, 240, width=640, height=480)
        self.assertEqual(quadrant_center, "center area")

    def test_object_tracker_mock(self):
        tracker = MemoraObjectTracker(mock_mode=True)
        # Create a mock frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # In mock mode, detect_objects returns simulated detections
        detections = tracker.detect_objects(frame)
        self.assertGreaterEqual(len(tracker.mock_detections), 1)
        
        # Verify format of detections
        for det in detections:
            self.assertIn("name", det)
            self.assertIn("box", det)
            self.assertIn("confidence", det)
            self.assertIn("center", det)
            self.assertEqual(len(det["box"]), 4)

    def test_database_object_tracking(self):
        # Initial states
        self.assertEqual(self.db.get_current_room(), "Living Room")
        
        # Set room
        self.db.set_current_room("Kitchen")
        self.assertEqual(self.db.get_current_room(), "Kitchen")

        # Log object
        success = self.db.log_object("cell phone", 320, 240, "Kitchen", (100, 100, 200, 200))
        self.assertTrue(success)

        # Get location
        info = self.db.get_last_known_location("cell phone")
        self.assertIsNotNone(info)
        self.assertEqual(info["room"], "Kitchen")
        self.assertAlmostEqual(info["x"], 320.0)
        self.assertEqual(info["bounding_box"], [100, 100, 200, 200])

        # Check history
        history = self.db.get_object_history("cell phone")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["room"], "Kitchen")

    def test_spatial_slam_visual(self):
        slam = MemoraSpatialSLAM(mock_mode=False)
        
        # Create test frames
        frame_red = np.zeros((100, 100, 3), dtype=np.uint8)
        frame_red[:, :, 2] = 255 # BGR -> Red
        
        frame_blue = np.zeros((100, 100, 3), dtype=np.uint8)
        frame_blue[:, :, 0] = 255 # BGR -> Blue

        # Register rooms
        slam.register_room("Red Room", frame_red)
        slam.register_room("Blue Room", frame_blue)

        # Classify
        room = slam.classify_room(frame_red)
        # First classification sets default or current
        self.assertEqual(room, "Red Room")

        # Classify Blue
        room = slam.classify_room(frame_blue)
        # Should transition
        self.assertEqual(room, "Blue Room")

        # Force transition
        slam.force_room_transition("Mock Zone")
        self.assertEqual(slam.current_room, "Mock Zone")

    def test_context_binder_query_parsing(self):
        binder = MemoraContextBinder(api_key=None) # force local fallback
        
        # Test case 1: simple location query
        res = binder.parse_location_query("Where is my phone?")
        self.assertEqual(res["target_object"], "phone")

        # Test case 2: query with action verb
        res = binder.parse_location_query("Where did I leave my keys?")
        self.assertEqual(res["target_object"], "keys")

        # Test case 3: non-matching query
        res = binder.parse_location_query("What time is it?")
        self.assertIsNone(res["target_object"])

if __name__ == "__main__":
    unittest.main()
