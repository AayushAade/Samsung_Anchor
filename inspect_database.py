#!/usr/bin/env python3
"""
MEMORA (Samsung Anchor) Database Inspection Tool
================================================
Standalone utility to inspect and audit SQLite database tables and FAISS vector embeddings.

Usage:
  python inspect_database.py [db_path]
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

from src.memory.database import MemoraDatabase, resolve_db_url
from src.memory.models import Identity, Object, ObjectHistory, EpisodeModel, RelevantMemoryModel, SystemState


def validate_database(db_path: str | None = None) -> bool:
    """
    Objectives 6 & 7: Database & FAISS Vector Store Consistency Checker.
    Audits DB tables, FAISS embeddings, orphan records, duplicates, storage size, and query latency.
    """
    import time
    import numpy as np

    # None resolves to the configured default (settings.DB_PATH / MEMORA_DB_PATH).
    target_path = db_path
    url, fs_path = resolve_db_url(target_path)
    file_bytes = os.path.getsize(fs_path) if fs_path and os.path.exists(fs_path) else 0
    file_mb = round(file_bytes / (1024 * 1024), 3)

    db = MemoraDatabase(target_path)
    issues = []

    print("\n🔍 RUNNING COMPREHENSIVE DATABASE & FAISS CONSISTENCY AUDIT...")
    print("=" * 65)
    print(f"  Target DB Path : {fs_path or target_path}")
    print(f"  Storage Size   : {file_mb} MB ({file_bytes} bytes)")

    with db._session_scope() as session:
        # 1. Orphan Identities Check
        identities = session.query(Identity).all()
        for idx in identities:
            if not idx.identity_id:
                issues.append("Identity row without identity_id found")

        # 2. Duplicate Objects & Memory Check
        objects = session.query(Object).all()
        obj_names = [o.name for o in objects]
        duplicates = set([x for x in obj_names if obj_names.count(x) > 1])
        if duplicates:
            issues.append(f"Duplicate object names found: {list(duplicates)}")

        # 3. Foreign Key Integrity Check (ObjectHistory -> Object)
        histories = session.query(ObjectHistory).all()
        for h in histories:
            if h.object_name not in obj_names:
                issues.append(f"Broken foreign key in ObjectHistory (id={h.id}): object '{h.object_name}' missing from Object table")

        # 4. Episode Integrity Check
        episodes = session.query(EpisodeModel).all()
        for ep in episodes:
            if not ep.summary or not ep.timestamp:
                issues.append(f"Invalid Episode (id={ep.id}): missing summary or timestamp")

        # 5. Memory Integrity Check
        memories = session.query(RelevantMemoryModel).all()
        for m in memories:
            if not m.title or not m.summary:
                issues.append(f"Invalid RelevantMemory (id={m.memory_id}): missing title or summary")

    # 6. SQLite <-> face-embedding store consistency
    integrity = db.check_integrity()
    if integrity["identities_without_embeddings"]:
        issues.append(f"{len(integrity['identities_without_embeddings'])} identities have no face embedding "
                      "(cannot be recognized until re-enrolled)")
    if integrity["orphan_embedding_identities"]:
        issues.append(f"Embeddings reference unknown identities: {integrity['orphan_embedding_identities']}")
    for key in ("vector_store_load_error", "vector_store_save_error"):
        if integrity[key]:
            issues.append(integrity[key])

    # 7. FAISS Embedding & Query Latency Audit
    faiss_cnt = db.vector_store.index.ntotal if hasattr(db, "vector_store") and db.vector_store else 0
    faiss_dim = db.vector_store.index.d if hasattr(db, "vector_store") and db.vector_store else 128
    query_latency_ms = 0.0

    if faiss_cnt > 0:
        t0 = time.perf_counter()
        sample_query = np.random.randn(1, faiss_dim).astype("float32")
        db.vector_store.find_match(sample_query[0], tolerance=0.6)
        query_latency_ms = round((time.perf_counter() - t0) * 1000.0, 3)

    print(f"  ✓ Identities Count      : {len(identities)}")
    print(f"  ✓ Objects Count         : {len(objects)}")
    print(f"  ✓ Object History Count  : {len(histories)}")
    print(f"  ✓ Episode Rows Count    : {len(episodes)}")
    print(f"  ✓ Memory Rows Count     : {len(memories)}")
    print(f"  ✓ FAISS Vector Count    : {faiss_cnt} ({faiss_dim}D Embeddings)")
    print(f"  ✓ FAISS Query Latency   : {query_latency_ms} ms (Target < 5.0ms)")

    print("-" * 65)
    if not issues:
        print("🟢 DATABASE & FAISS AUDIT RESULT: PASS (0 Integrity Errors)")
        print("=" * 65 + "\n")
        return True
    else:
        print(f"🔴 DATABASE & FAISS AUDIT RESULT: FAIL ({len(issues)} Issues Found):")
        for iss in issues:
            print(f"   ⚠️  {iss}")
        print("=" * 65 + "\n")
        return False


def inspect_database(db_path: str | None = None) -> None:
    target_path = db_path
    url, fs_path = resolve_db_url(target_path)

    print("=" * 60)
    print("🧠 MEMORA Database Inspection Tool")
    print("============================================================")
    print(f"  Target File : {fs_path or target_path}")
    print(f"  SQLAlchemy  : {url}")
    exists = os.path.exists(fs_path) if fs_path else True
    print(f"  File Status : {'EXISTS' if exists else 'NEW (Will initialize on access)'}")
    print("=" * 60)

    db = MemoraDatabase(target_path)

    # 1. Table Row Statistics
    print("\n📊 1. DATABASE TABLE ROW STATISTICS")
    print("-" * 60)
    with db._session_scope() as session:
        identities_cnt = session.query(Identity).count()
        objects_cnt = session.query(Object).count()
        history_cnt = session.query(ObjectHistory).count()
        episodes_cnt = session.query(EpisodeModel).count()
        memories_cnt = session.query(RelevantMemoryModel).count()
        sysstate_cnt = session.query(SystemState).count()

    print(f"  Identities (People)     : {identities_cnt}")
    print(f"  Objects (Spatial)       : {objects_cnt}")
    print(f"  Object Spatial History  : {history_cnt}")
    print(f"  Episodes (Daily Log)    : {episodes_cnt}")
    print(f"  Relevant Memories       : {memories_cnt}")
    print(f"  System State Settings   : {sysstate_cnt}")

    # 2. Identified People & FAISS Vector Store
    print("\n👤 2. IDENTIFIED PEOPLE & FAISS VECTOR STORE")
    print("-" * 60)
    faiss_ntotal = db.vector_store.index.ntotal if hasattr(db, "vector_store") and db.vector_store else 0
    faiss_index_file = db.vector_store.index_path if hasattr(db, "vector_store") else "N/A"
    faiss_map_file = db.vector_store.mapping_path if hasattr(db, "vector_store") else "N/A"
    print(f"  FAISS Index Vector Count: {faiss_ntotal} (Dimensionality: 128D)")
    print(f"  FAISS Index File        : {faiss_index_file} ({'EXISTS' if faiss_index_file and os.path.exists(faiss_index_file) else 'NOT FOUND'})")
    print(f"  FAISS Mapping File      : {faiss_map_file} ({'EXISTS' if faiss_map_file and os.path.exists(faiss_map_file) else 'NOT FOUND'})")
    integrity = db.check_integrity()
    if not integrity["ok"]:
        print("  ⚠️  Identity/embedding store is inconsistent:")
        if integrity["identities_without_embeddings"]:
            print(f"     {len(integrity['identities_without_embeddings'])} identities have no stored face embedding "
                  "(they cannot be recognized until re-enrolled).")
        if integrity["orphan_embedding_identities"]:
            print(f"     Embeddings exist for unknown identities: {integrity['orphan_embedding_identities']}")
        for key in ("vector_store_load_error", "vector_store_save_error"):
            if integrity[key]:
                print(f"     {integrity[key]}")

    all_identities = db.get_all_identities()
    if not all_identities:
        print("  No identity records stored yet.")
    else:
        for ident_id, info in all_identities.items():
            name = info.get("display_name") or info.get("candidate_name") or ident_id
            rel = info.get("relationship") or "Unknown"
            seen = info.get("times_seen", 1)
            last_seen = info.get("last_seen") or "Never"
            emb_cnt = len(info.get("embeddings", []))
            print(f"  • ID: {ident_id:<12} | Name: {name:<18} | Rel: {rel:<12} | Times Seen: {seen:<3} | FAISS Embeddings: {emb_cnt} | Last Seen: {last_seen}")

    # 3. Observed Objects & Spatial Memory
    print("\n👓 3. OBSERVED OBJECTS & SPATIAL MEMORY")
    print("-" * 60)
    with db._session_scope() as session:
        all_objects = session.query(Object).all()
        if not all_objects:
            print("  No spatial objects logged yet.")
        else:
            for obj in all_objects:
                obj_name = obj.name or "Item"
                room = obj.room or "Living Room"
                last_seen = str(obj.last_seen) if obj.last_seen else "Recently"
                bbox = obj.bounding_box or []
                print(f"  • Object: {obj_name:<20} | Last Room: {room:<14} | Last Seen: {last_seen:<10} | BBox: {bbox}")

    # 4. Episodes & Daily Timeline Records
    print("\n📅 4. EPISODES & DAILY TIMELINE RECORDS")
    print("-" * 60)
    episodes = db.episode_repo.get_recent_episodes(limit=5) if hasattr(db, "episode_repo") else []
    if not episodes:
        print("  No episodes recorded yet.")
    else:
        for ep in episodes:
            t_str = ep.timestamp.strftime("%H:%M:%S") if isinstance(ep.timestamp, datetime) else str(ep.timestamp)
            person = ep.person or "System"
            loc = ep.location or "Home"
            print(f"  • [{t_str}] ({person} @ {loc}) : {ep.summary}")

    # 5. Stored Preferences & Fact Memories
    print("\n🧠 5. STORED PREFERENCES & FACT MEMORIES")
    print("-" * 60)
    pref_mems = db.memory_repo.find(tags=["user_preference", "user_fact"]) if hasattr(db, "memory_repo") else []
    if not pref_mems:
        print("  No preference/fact memories stored yet.")
    else:
        for m in pref_mems:
            print(f"  • Memory ID: {m.memory_id} | Title: {m.title} | Fact: {m.summary}")

    print("\n" + "=" * 60)
    print("🟢 Database Inspection Complete.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--validate":
        target_path = sys.argv[2] if len(sys.argv) > 2 else None
        success = validate_database(target_path)
        sys.exit(0 if success else 1)
    else:
        db_path = sys.argv[1] if len(sys.argv) > 1 else None
        inspect_database(db_path)
