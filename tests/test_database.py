import unittest
import os
import json
from pathlib import Path
import numpy as np

from core.database import MemoraDatabase

class TestMemoraDatabase(unittest.TestCase):
    def setUp(self):
        self.test_db_path = "test_memora_db.json"
        # Ensure clean file
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = MemoraDatabase(db_path=self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_initial_state(self):
        self.assertEqual(len(self.db.get_all_identities()), 0)
        self.assertEqual(self.db.data["next_anon_index"], 1)

    def test_register_anonymous(self):
        embedding = np.random.rand(128)
        anon_id = self.db.register_anonymous(embedding)
        
        self.assertEqual(anon_id, "Anonymous_ID_1")
        self.assertEqual(len(self.db.get_all_identities()), 1)
        
        identity = self.db.get_identity(anon_id)
        self.assertIsNotNone(identity)
        self.assertIsNone(identity["name"])
        self.assertIsNone(identity["relationship"])
        self.assertEqual(len(identity["embeddings"]), 1)
        # Check float conversion
        self.assertAlmostEqual(identity["embeddings"][0][0], embedding[0])

    def test_find_match_exact(self):
        embedding = np.random.rand(128)
        anon_id = self.db.register_anonymous(embedding)
        
        # Test exact match
        matched_id, info, dist = self.db.find_match(embedding, tolerance=0.1)
        self.assertEqual(matched_id, anon_id)
        self.assertAlmostEqual(dist, 0.0)

    def test_find_match_close(self):
        embedding = np.ones(128) * 0.5
        anon_id = self.db.register_anonymous(embedding)
        
        # Small perturbation (within tolerance)
        query_embedding = embedding.copy()
        query_embedding[0] += 0.02
        
        matched_id, info, dist = self.db.find_match(query_embedding, tolerance=0.6)
        self.assertEqual(matched_id, anon_id)
        self.assertLess(dist, 0.6)

    def test_find_no_match_far(self):
        embedding_1 = np.ones(128) * 0.1
        self.db.register_anonymous(embedding_1)
        
        # Completely different embedding
        query_embedding = np.ones(128) * 0.9
        matched_id, info, dist = self.db.find_match(query_embedding, tolerance=0.6)
        self.assertIsNone(matched_id)

    def test_bind_name(self):
        embedding = np.random.rand(128)
        anon_id = self.db.register_anonymous(embedding)
        
        # Bind name
        success = self.db.bind_name(anon_id, "Sarah", "Daughter")
        self.assertTrue(success)
        
        identity = self.db.get_identity(anon_id)
        self.assertEqual(identity["name"], "Sarah")
        self.assertEqual(identity["relationship"], "Daughter")

    def test_persistence(self):
        embedding = np.random.rand(128)
        anon_id = self.db.register_anonymous(embedding)
        self.db.bind_name(anon_id, "Mark", "Son")
        
        # Create a new database instance pointing to the same file
        db2 = MemoraDatabase(db_path=self.test_db_path)
        identity = db2.get_identity(anon_id)
        self.assertIsNotNone(identity)
        self.assertEqual(identity["name"], "Mark")
        self.assertEqual(identity["relationship"], "Son")

if __name__ == "__main__":
    unittest.main()
