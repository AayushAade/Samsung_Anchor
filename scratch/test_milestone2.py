import time
import os
import sys
# Add project root to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.coordinator.anchor_coordinator import AnchorCoordinator
from src.pipeline.cognitive_pipeline import CognitivePipeline

class MockRecognizer:
    def process_frame(self, frame, database):
        # Simulate Vision taking ~20ms
        time.sleep(0.02)
        return {"face_id": "Anonymous_ID_1", "name": "Sarah", "relationship": "Daughter"}

class _FakeQuery:
    def filter_by(self, **kw): return self
    def first(self): return None
    def all(self): return []

class MockSessionFactory:
    def __call__(self): return self
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def query(self, *args): return _FakeQuery()
    def commit(self): pass
    def add(self, *args): pass

class MockMemoryRepo:
    def find(self, query): return []
    def save(self, memory): pass

class MockDatabase:
    def __init__(self):
        self.memory_repo = MockMemoryRepo()
        self.SessionFactory = MockSessionFactory()

class MockListener:
    pass

class MockBinder:
    pass

def main():
    print("Testing Milestone 2 Async Event Bus...")
    
    # We must patch the PresenceEngine inside CognitivePipeline to not require a real DB for this test,
    # or just let it run. The default CognitivePipeline uses MemoryRepository (which is in-memory).
    
    coordinator = AnchorCoordinator(
        database=MockDatabase(),
        recognizer=MockRecognizer(),
        listener=MockListener(),
        binder=MockBinder(),
        speaker=None
    )
    
    coordinator.initialize()
    coordinator.start()
    
    print("Simulating 30 FPS camera loop for 100 frames...")
    
    start_time = time.time()
    
    for i in range(100):
        frame_start = time.time()
        
        # Simulate OpenCV capture (10ms)
        time.sleep(0.01)
        
        # Pass to coordinator
        coordinator.process_frame(None)
        
        # Consume any actions that happened asynchronously
        actions = coordinator.consume_actions()
        if actions:
            print(f"Frame {i}: Generated {len(actions)} actions! {actions[0].message}")
        
        frame_end = time.time()
        # Should be ~30ms total per frame loop (20ms vision + 10ms capture). If Pipeline was synchronous, it would be much slower.
        if (frame_end - frame_start) > 0.05:
            print(f"WARNING: Frame {i} took too long! {(frame_end - frame_start)*1000:.1f}ms")
            
    total_time = time.time() - start_time
    print(f"Total time for 100 frames: {total_time:.2f} seconds.")
    print(f"Effective FPS: {100 / total_time:.1f}")
    
    coordinator.shutdown()
    
    if total_time < 4.0:
        print("Success! The pipeline did not block the camera loop.")
    else:
        print("Failed! The pipeline is still blocking.")

if __name__ == "__main__":
    main()
