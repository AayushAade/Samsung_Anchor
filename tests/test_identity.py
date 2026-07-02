import unittest
import numpy as np
import os

from core.database import MemoraDatabase
from core.face_recognizer import MemoraFaceRecognizer
from core.context_binder import MemoraContextBinder

class TestIdentityBinding(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test_identity_db.json"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = MemoraDatabase(db_path=self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_face_recognizer_mock_mode(self):
        recognizer = MemoraFaceRecognizer(tolerance=0.6, mock_mode=True)
        # Create a mock BGR frame
        frame = 128 * np.ones((480, 640, 3), dtype=np.uint8)
        
        # Process frame - should register a new Anonymous face
        results = recognizer.process_frame(frame, self.db)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["face_id"], "Anonymous_ID_1")
        self.assertTrue(results[0]["is_new"])
        self.assertIsNone(results[0]["name"])

        # Process frame again - should find existing match in database (not new)
        results2 = recognizer.process_frame(frame, self.db)
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0]["face_id"], "Anonymous_ID_1")
        self.assertFalse(results2[0]["is_new"])

    def test_context_binder_local_parsing(self):
        binder = MemoraContextBinder(api_key=None) # force local fallback
        
        # Test case 1: Daughter introduction
        res1 = binder.parse_transcript("Hi Dad, it's Sarah")
        self.assertEqual(res1["extracted_name"], "Sarah")
        self.assertIn(res1["relationship"], ["Daughter", "Child"])

        # Test case 2: Son introduction
        res2 = binder.parse_transcript("Hello, it's your son Mark")
        self.assertEqual(res2["extracted_name"], "Mark")
        self.assertEqual(res2["relationship"], "Son")

        # Test case 3: Simple name statement
        res3 = binder.parse_transcript("My name is John")
        self.assertEqual(res3["extracted_name"], "John")
        self.assertIsNone(res3["relationship"])

        # Test case 4: Simple greeting without name
        res4 = binder.parse_transcript("Hello, how are you today?")
        self.assertIsNone(res4["extracted_name"])
        self.assertIsNone(res4["relationship"])

        # Test case 5: Implied granddaughter introduction
        res5 = binder.parse_transcript("Hi Grandma, it's your granddaughter Jessica")
        self.assertEqual(res5["extracted_name"], "Jessica")
        self.assertEqual(res5["relationship"], "Granddaughter")

if __name__ == "__main__":
    unittest.main()
