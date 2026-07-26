from pprint import pprint

from src.memory.database import MemoraDatabase
from src.pipeline.cognitive_pipeline import CognitivePipeline

db = MemoraDatabase("sqlite:///:memory:")
pipeline = CognitivePipeline(db)

frame = pipeline.runtime_manager.camera.capture_frame()

print("\nReturned object type:")
print(type(frame))

print("\nReturned object:")
pprint(frame)

if isinstance(frame, dict):
    print("\nKeys:")
    print(frame.keys())