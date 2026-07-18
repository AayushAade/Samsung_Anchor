import os
import sys
# Add project root to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.memory.database import MemoraDatabase

def main():
    print("Testing Milestone 1 DB...")
    db = MemoraDatabase()
    db.clear() # Fresh start
    
    print("1. Testing Identity Registration & Vector Store...")
    embedding = np.random.rand(128).astype(np.float32)
    embedding /= np.linalg.norm(embedding)
    
    anon_id = db.register_anonymous(embedding)
    print(f"Registered: {anon_id}")
    
    print("2. Testing Find Match...")
    query_emb = embedding + (np.random.rand(128).astype(np.float32) * 0.05)
    match_id, info, dist = db.find_match(query_emb, tolerance=0.4)
    print(f"Match ID: {match_id}, Distance: {dist}")
    
    assert match_id == anon_id, "Match failed!"
    
    print("3. Testing Evidence Accumulation...")
    res1 = db.add_evidence(anon_id, "Sarah", "Daughter")
    print("Evidence 1:", res1)
    res2 = db.add_evidence(anon_id, "Sarah", "Daughter")
    print("Evidence 2:", res2)
    
    info = db.get_identity(anon_id)
    print("Updated Identity Status:", info['status'])
    
    print("4. Testing Object Logging...")
    db.log_object("keys", 10.5, 20.2, "Living Room")
    loc = db.get_last_known_location("keys")
    print("Keys location:", loc['room'], loc['x'], loc['y'])
    
    print("All basic operations passed!")

if __name__ == "__main__":
    main()
