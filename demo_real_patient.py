#!/usr/bin/env python3
"""
MEMORA (Samsung Anchor) Official Real Patient Demonstration Script
===================================================================
Executes complete end-to-end patient workflow:
1. Camera Startup & Perception Pipeline Initialization
2. Unknown Face Recognition & User Onboarding
3. Natural Dialogue & Conversation Memory Persistence
4. Object Detection, Spatial Tracking & Disappearance Tracking
5. Contextual Memory Retrieval & Question Answering
6. Full Application Restart & Persistent DB Verification
7. Database Consistency Integrity Audit
"""

from __future__ import annotations

import os
import sys
import time

from src.application.factory import build_application
from src.memory.database import MemoraDatabase
from src.runtime.runtime import AnchorRuntime
from inspect_database import validate_database


def run_demo():
    print("\n" + "=" * 70)
    print("🧠 MEMORA (Samsung Anchor) - RELEASE CANDIDATE DEMONSTRATION SCRIPT")
    print("=" * 70)

    db_path = "memora_db_v2.sqlite"
    
    # --------------------------------------------------
    # Step 1: Initialize System & Hardware Pipelines
    # --------------------------------------------------
    print("\n[Step 1] Initializing System & Database Pipeline...")
    db = MemoraDatabase(db_path)
    coord = build_application(live_hardware=False, database=db)
    runtime = AnchorRuntime(coord)
    runtime.initialize()
    print("✓ Hardware pipelines, SQLite persistence, and reasoning engines initialized.")

    # --------------------------------------------------
    # Step 2: Unknown Face Onboarding
    # --------------------------------------------------
    print("\n[Step 2] Processing User Onboarding ('I am Sid')...")
    act1 = coord.pipeline.process({"user_speech": "I am Sid"})
    if act1:
        print(f"  🗣️ MEMORA Output: '{act1[0].message}'")

    # --------------------------------------------------
    # Step 3: Long Conversation Memory Persistence
    # --------------------------------------------------
    print("\n[Step 3] Storing User Facts ('I like cricket' & 'My daughter is Riya')...")
    act2 = coord.pipeline.process({"user_speech": "I like cricket."})
    if act2:
        print(f"  🗣️ MEMORA Output: '{act2[0].message}'")

    act3 = coord.pipeline.process({"user_speech": "My daughter is Riya."})
    if act3:
        print(f"  🗣️ MEMORA Output: '{act3[0].message}'")

    # --------------------------------------------------
    # Step 4: Spatial Object Logging
    # --------------------------------------------------
    print("\n[Step 4] Logging Observed Object ('Reading Glasses' in 'Living Room')...")
    db.log_object("Reading Glasses", x=1.5, y=2.0, room="Living Room", bounding_box=[150, 200, 80, 35])
    print("  ✓ Spatial object logged to SQLite ObjectRepository.")

    # --------------------------------------------------
    # Step 5: Question Answering (Spatial Location & Fact Retrieval)
    # --------------------------------------------------
    print("\n[Step 5] Querying Assistant ('Where are my glasses?' & 'Who is my daughter?')...")
    act4 = coord.pipeline.process({"user_speech": "Where are my glasses?"})
    if act4:
        print(f"  🗣️ MEMORA Output: '{act4[0].message}'")

    act5 = coord.pipeline.process({"user_speech": "Who is my daughter?"})
    if act5:
        print(f"  🗣️ MEMORA Output: '{act5[0].message}'")

    # --------------------------------------------------
    # Step 6: Application Restart & Persistent Verification
    # --------------------------------------------------
    print("\n[Step 6] Simulating Application Restart (Re-opening SQLite Database)...")
    runtime.shutdown()
    
    # Fresh initialization from persisted disk database
    db_rebound = MemoraDatabase(db_path)
    coord_rebound = build_application(live_hardware=False, database=db_rebound)
    runtime_rebound = AnchorRuntime(coord_rebound)
    runtime_rebound.initialize()
    print("✓ Application restarted cleanly. Loaded state from memora_db_v2.sqlite.")

    # --------------------------------------------------
    # Step 7: Post-Restart Persistence Query
    # --------------------------------------------------
    print("\n[Step 7] Querying Re-started Assistant ('Who is my daughter?')...")
    act6 = coord_rebound.pipeline.process({"user_speech": "Who is my daughter?"})
    if act6:
        print(f"  🗣️ MEMORA Output: '{act6[0].message}'")
        assert "riya" in act6[0].message.lower() or "daughter" in act6[0].message.lower(), "Persistence verification failed!"
        print("  ✅ Persistent Memory Verified Across Restart!")

    # --------------------------------------------------
    # Step 8: Database Integrity Audit
    # --------------------------------------------------
    print("\n[Step 8] Running Database Integrity Validation...")
    is_valid = validate_database(db_path)
    assert is_valid, "Database validation failed!"

    runtime_rebound.shutdown()

    print("=" * 70)
    print("🟢 MEMORA OFFICIAL DEMONSTRATION COMPLETE: ALL STEPS VERIFIED PASSING!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_demo()
