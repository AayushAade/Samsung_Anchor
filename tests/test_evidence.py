import unittest
import os
import numpy as np

from core.database import MemoraDatabase
from core.context_binder import MemoraContextBinder

class TestEvidenceAccumulation(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test_evidence_db.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = MemoraDatabase(db_path=self.test_db_path)
        
        # Register a mock face
        self.mock_embedding = np.random.rand(128)
        self.face_id = self.db.register_anonymous(self.mock_embedding)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_evidence_accumulation_no_relation(self):
        # 1. First hearing (no relationship) -> 40%
        res = self.db.add_evidence(self.face_id, "Mark")
        self.assertEqual(res["name"], "Mark")
        self.assertIsNone(res["relationship"])
        self.assertEqual(res["confidence"], 0.40)
        self.assertFalse(res["is_confirmed"])
        
        # Verify identity remains anonymous in database
        identity = self.db.get_identity(self.face_id)
        self.assertIsNone(identity["name"])
        
        # 2. Second hearing (no relationship) -> 70%
        res = self.db.add_evidence(self.face_id, "Mark")
        self.assertEqual(res["confidence"], 0.70)
        self.assertFalse(res["is_confirmed"])
        
        identity = self.db.get_identity(self.face_id)
        self.assertIsNone(identity["name"])

        # 3. Third hearing (no relationship) -> 80% (confirmed!)
        res = self.db.add_evidence(self.face_id, "Mark")
        self.assertEqual(res["confidence"], 0.80)
        self.assertTrue(res["is_confirmed"])
        
        identity = self.db.get_identity(self.face_id)
        self.assertEqual(identity["name"], "Mark")
        self.assertIsNone(identity["relationship"])

    def test_evidence_accumulation_with_relation(self):
        # Hearing with relationship -> 90% (confirmed!)
        res = self.db.add_evidence(self.face_id, "Priya", "Daughter")
        self.assertEqual(res["name"], "Priya")
        self.assertEqual(res["relationship"], "Daughter")
        self.assertEqual(res["confidence"], 0.90)
        self.assertTrue(res["is_confirmed"])
        
        identity = self.db.get_identity(self.face_id)
        self.assertEqual(identity["name"], "Priya")
        self.assertEqual(identity["relationship"], "Daughter")

    def test_evidence_accumulation_mixed_flow(self):
        # 1. First hearing: "Hi Mark" -> 40% (unconfirmed)
        res1 = self.db.add_evidence(self.face_id, "Mark")
        self.assertEqual(res1["confidence"], 0.40)
        
        # 2. Second hearing: "Mark, your daughter is calling" -> 85% (confirmed!)
        res2 = self.db.add_evidence(self.face_id, "Mark", "Daughter")
        self.assertEqual(res2["confidence"], 0.85)
        self.assertTrue(res2["is_confirmed"])
        
        identity = self.db.get_identity(self.face_id)
        self.assertEqual(identity["name"], "Mark")
        self.assertEqual(identity["relationship"], "Daughter")

    def test_get_candidates(self):
        # Add multiple competing candidates
        self.db.add_evidence(self.face_id, "Mark")
        self.db.add_evidence(self.face_id, "Priya")
        self.db.add_evidence(self.face_id, "Priya") # Priya count=2, conf=70%
        
        candidates = self.db.get_candidates(self.face_id)
        self.assertEqual(len(candidates), 2)
        
        # Priya should be first (conf 70%) and Mark second (conf 40%)
        self.assertEqual(candidates[0]["name"], "Priya")
        self.assertEqual(candidates[0]["confidence"], 0.70)
        self.assertEqual(candidates[1]["name"], "Mark")
        self.assertEqual(candidates[1]["confidence"], 0.40)

    def test_context_binder_new_heuristic(self):
        binder = MemoraContextBinder(api_key=None) # force offline parser
        res = binder.parse_transcript("Mark, your daughter is calling")
        self.assertEqual(res["extracted_name"], "Mark")
        self.assertEqual(res["relationship"], "Daughter")

        # Test free-form name extraction from conversational contexts
        res2 = binder.parse_transcript("Hey, what's up Sid")
        self.assertEqual(res2["extracted_name"], "Sid")

        res3 = binder.parse_transcript("Sid you forgot your lunch")
        self.assertEqual(res3["extracted_name"], "Sid")

if __name__ == "__main__":
    unittest.main()
