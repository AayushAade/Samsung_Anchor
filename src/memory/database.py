import json
import os
import sqlite3
import threading
from datetime import datetime
import numpy as np

# Import app settings
from config import settings

class MemoraDatabase:
    def __init__(self, db_path=None):
        self.db_path = db_path or settings.DB_PATH
        self.lock = threading.Lock()
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        # Check if the file is a JSON file or invalid database
        if os.path.exists(self.db_path) and os.path.getsize(self.db_path) > 0:
            try:
                conn = sqlite3.connect(self.db_path)
                conn.execute("SELECT 1")
                conn.close()
            except sqlite3.DatabaseError:
                print(f"[Database Warning] Invalid database file detected at {self.db_path}. Replacing with new SQLite database.")
                backup_path = self.db_path + ".old_json"
                try:
                    if os.path.exists(backup_path):
                        os.remove(backup_path)
                    os.rename(self.db_path, backup_path)
                except Exception as e:
                    print(f"[Database Warning] Failed to backup old database: {e}. Deleting.")
                    try:
                        os.remove(self.db_path)
                    except Exception:
                        pass

        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check table columns of identities. If name column exists instead of display_name, it's the old schema.
            # We should drop all old tables to start fresh!
            try:
                cursor.execute("PRAGMA table_info(identities)")
                columns = [col[1] for col in cursor.fetchall()]
                if columns and "name" in columns and "display_name" not in columns:
                    print("[Database Migration] Old identities table schema detected. Dropping tables to migrate to clean schema.")
                    cursor.execute("DROP TABLE IF EXISTS system_state")
                    cursor.execute("DROP TABLE IF EXISTS identities")
                    cursor.execute("DROP TABLE IF EXISTS face_embeddings")
                    cursor.execute("DROP TABLE IF EXISTS identity_evidence")
                    cursor.execute("DROP TABLE IF EXISTS objects")
                    cursor.execute("DROP TABLE IF EXISTS object_history")
            except Exception:
                pass
            
            # system_state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # New identities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS identities (
                    identity_id TEXT PRIMARY KEY,
                    display_name TEXT,
                    relationship TEXT,
                    status TEXT,
                    candidate_name TEXT,
                    candidate_relationship TEXT,
                    confidence REAL DEFAULT 0.0,
                    times_seen INTEGER DEFAULT 1,
                    first_seen TEXT,
                    last_seen TEXT,
                    evidence_history TEXT
                )
            """)
            
            # face_embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identity_id TEXT,
                    embedding TEXT,
                    FOREIGN KEY(identity_id) REFERENCES identities(identity_id) ON DELETE CASCADE
                )
            """)
            
            # identity_evidence table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS identity_evidence (
                    identity_id TEXT,
                    heard_name TEXT,
                    heard_relationship TEXT,
                    count INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT,
                    updated_at TEXT,
                    PRIMARY KEY(identity_id, heard_name),
                    FOREIGN KEY(identity_id) REFERENCES identities(identity_id) ON DELETE CASCADE
                )
            """)
            
            # objects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS objects (
                    name TEXT PRIMARY KEY,
                    last_seen TEXT,
                    x REAL,
                    y REAL,
                    room TEXT,
                    bounding_box TEXT
                )
            """)
            
            # object_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS object_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_name TEXT,
                    timestamp TEXT,
                    x REAL,
                    y REAL,
                    room TEXT,
                    bounding_box TEXT,
                    FOREIGN KEY(object_name) REFERENCES objects(name) ON DELETE CASCADE
                )
            """)
            
            # Initialize default system states if not present
            cursor.execute("INSERT OR IGNORE INTO system_state (key, value) VALUES ('next_anon_index', '1')")
            cursor.execute("INSERT OR IGNORE INTO system_state (key, value) VALUES ('current_room', 'Living Room')")
            
            conn.commit()
            conn.close()

    def _get_system_state(self, key, default=None):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_state WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default

    def _set_system_state(self, key, value):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO system_state (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()

    @property
    def data(self):
        """Compatibility property for old unit tests accessing db.data directly."""
        next_anon = int(self._get_system_state("next_anon_index", 1))
        current_room = self._get_system_state("current_room", "Living Room")
        
        identities = self.get_all_identities()
        
        objects_dict = {}
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, last_seen, x, y, room, bounding_box FROM objects")
        rows = cursor.fetchall()
        for r in rows:
            obj_name = r["name"]
            cursor.execute("SELECT timestamp, x, y, room, bounding_box FROM object_history WHERE object_name = ? ORDER BY id ASC", (obj_name,))
            hist_rows = cursor.fetchall()
            history = []
            for h in hist_rows:
                history.append({
                    "timestamp": h["timestamp"],
                    "x": h["x"],
                    "y": h["y"],
                    "room": h["room"],
                    "bounding_box": json.loads(h["bounding_box"]) if h["bounding_box"] else None
                })
            objects_dict[obj_name] = {
                "last_seen": r["last_seen"],
                "x": r["x"],
                "y": r["y"],
                "room": r["room"],
                "bounding_box": json.loads(r["bounding_box"]) if r["bounding_box"] else None,
                "history": history
            }
        conn.close()
        
        return {
            "identities": identities,
            "next_anon_index": next_anon,
            "objects": objects_dict,
            "current_room": current_room
        }

    def load(self):
        pass

    def save(self):
        pass

    def find_match(self, query_embedding, tolerance=None):
        """
        Compares query_embedding (128D list/array) against all stored identities.
        Returns (identity_id, identity_dict, distance) if a match is found under tolerance,
        otherwise returns (None, None, None).
        """
        if tolerance is None:
            tolerance = settings.FACE_TOLERANCE

        query_vector = np.array(query_embedding)
        best_match_id = None
        best_distance = float("inf")
        best_emb_id = None

        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, identity_id, embedding FROM face_embeddings")
            rows = cursor.fetchall()
            
            for r in rows:
                identity_id = r["identity_id"]
                emb_id = r["id"]
                stored_embedding = json.loads(r["embedding"])
                stored_vector = np.array(stored_embedding)
                distance = np.linalg.norm(query_vector - stored_vector)
                
                if distance < tolerance and distance < best_distance:
                    best_distance = distance
                    best_match_id = identity_id
                    best_emb_id = emb_id
            
            conn.close()
            
            if best_match_id is not None:
                identity_info = self.get_identity(best_match_id)
                if identity_info:
                    identity_info["embedding_row_id"] = best_emb_id
                return best_match_id, identity_info, best_distance

        return None, None, None

    def register_anonymous(self, embedding):
        """
        Registers a new anonymous identity with the given embedding vector.
        Returns the generated identity_id.
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT value FROM system_state WHERE key = 'next_anon_index'")
            anon_index = int(cursor.fetchone()[0])
            anon_id = f"Anonymous_ID_{anon_index}"
            
            cursor.execute("UPDATE system_state SET value = ? WHERE key = 'next_anon_index'", (str(anon_index + 1),))
            
            now_str = datetime.now().isoformat()
            cursor.execute(
                """INSERT INTO identities 
                   (identity_id, display_name, relationship, status, candidate_name, candidate_relationship, confidence, times_seen, first_seen, last_seen, evidence_history) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (anon_id, None, None, "unconfirmed", None, None, 0.0, 1, now_str, now_str, json.dumps([]))
            )
            
            embedding_json = json.dumps(list(embedding))
            cursor.execute(
                "INSERT INTO face_embeddings (identity_id, embedding) VALUES (?, ?)",
                (anon_id, embedding_json)
            )
            
            conn.commit()
            conn.close()
            return anon_id

    def add_embedding_to_identity(self, identity_id, embedding):
        """Adds a new embedding vector to an existing identity's database profile (for model reinforcement)."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM identities WHERE identity_id = ?", (identity_id,))
            if not cursor.fetchone():
                conn.close()
                return False
                
            now_str = datetime.now().isoformat()
            cursor.execute("UPDATE identities SET last_seen = ? WHERE identity_id = ?", (now_str, identity_id))
            
            embedding_json = json.dumps(list(embedding))
            cursor.execute(
                "INSERT INTO face_embeddings (identity_id, embedding) VALUES (?, ?)",
                (identity_id, embedding_json)
            )
            
            conn.commit()
            conn.close()
            return True

    def update_embedding_ema(self, embedding_id, new_embedding, alpha=0.1):
        """Updates a specific stored embedding using an Exponential Moving Average (EMA)."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT embedding FROM face_embeddings WHERE id = ?", (embedding_id,))
            row = cursor.fetchone()
            if row:
                stored = json.loads(row[0])
                stored_vector = np.array(stored)
                new_vector = np.array(new_embedding)
                updated_vector = alpha * new_vector + (1 - alpha) * stored_vector
                cursor.execute(
                    "UPDATE face_embeddings SET embedding = ? WHERE id = ?",
                    (json.dumps(list(updated_vector)), embedding_id)
                )
                conn.commit()
            conn.close()

    def increment_times_seen(self, identity_id):
        """Increments the times_seen counter for an identity and updates its last_seen timestamp."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            now_str = datetime.now().isoformat()
            cursor.execute(
                "UPDATE identities SET times_seen = times_seen + 1, last_seen = ? WHERE identity_id = ?",
                (now_str, identity_id)
            )
            conn.commit()
            conn.close()

    def bind_name(self, identity_id, name, relationship=None):
        """
        Binds a name and optional relationship to an existing anonymous or known identity_id.
        Sets status to 'confirmed' and confidence to 1.0.
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM identities WHERE identity_id = ?", (identity_id,))
            if not cursor.fetchone():
                conn.close()
                return False
                
            now_str = datetime.now().isoformat()
            cursor.execute(
                "UPDATE identities SET display_name = ?, relationship = ?, status = 'confirmed', confidence = 1.0, last_seen = ? WHERE identity_id = ?",
                (name, relationship, now_str, identity_id)
            )
                
            conn.commit()
            conn.close()
            return True

    def get_identity(self, identity_id):
        """Retrieves identity information for a given identity_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT display_name, relationship, status, candidate_name, candidate_relationship, 
                      confidence, times_seen, first_seen, last_seen, evidence_history 
               FROM identities WHERE identity_id = ?""",
            (identity_id,)
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        cursor.execute("SELECT embedding FROM face_embeddings WHERE identity_id = ?", (identity_id,))
        emb_rows = cursor.fetchall()
        embeddings = [json.loads(r["embedding"]) for r in emb_rows]
        
        conn.close()
        
        ev_history = []
        if row["evidence_history"]:
            try:
                ev_history = json.loads(row["evidence_history"])
            except Exception:
                pass

        return {
            "identity_id": identity_id,
            "display_name": row["display_name"],
            "relationship": row["relationship"],
            "status": row["status"],
            "candidate_name": row["candidate_name"],
            "candidate_relationship": row["candidate_relationship"],
            "confidence": row["confidence"],
            "times_seen": row["times_seen"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "evidence_history": ev_history,
            "embeddings": embeddings,
            # Old keys for backward compatibility:
            "name": row["display_name"],
            "created_at": row["first_seen"],
            "updated_at": row["last_seen"]
        }

    def get_all_identities(self):
        """Returns all identity records."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT identity_id FROM identities")
        rows = cursor.fetchall()
        
        identities_dict = {}
        for r in rows:
            identity_id = r["identity_id"]
            identities_dict[identity_id] = self.get_identity(identity_id)
            
        conn.close()
        return identities_dict

    def log_object(self, object_name, x, y, room, bounding_box=None):
        """
        Logs the detection of an object with its coordinates, room, and optional bounding box.
        Updates the last known location and adds to the historical log.
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            now_str = datetime.now().isoformat()
            bbox_json = json.dumps(list(bounding_box)) if bounding_box is not None else None
            
            cursor.execute(
                """
                INSERT INTO objects (name, last_seen, x, y, room, bounding_box)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    last_seen = excluded.last_seen,
                    x = excluded.x,
                    y = excluded.y,
                    room = excluded.room,
                    bounding_box = excluded.bounding_box
                """,
                (object_name, now_str, float(x), float(y), room, bbox_json)
            )
            
            cursor.execute(
                "INSERT INTO object_history (object_name, timestamp, x, y, room, bounding_box) VALUES (?, ?, ?, ?, ?, ?)",
                (object_name, now_str, float(x), float(y), room, bbox_json)
            )
            
            # Enforce history limit of 50 sightings
            cursor.execute("SELECT id FROM object_history WHERE object_name = ? ORDER BY id ASC", (object_name,))
            hist_ids = [r[0] for r in cursor.fetchall()]
            if len(hist_ids) > 50:
                excess_count = len(hist_ids) - 50
                placeholders = ",".join("?" for _ in range(excess_count))
                cursor.execute(
                    f"DELETE FROM object_history WHERE id IN ({placeholders})",
                    hist_ids[:excess_count]
                )
                
            conn.commit()
            conn.close()
            return True

    def get_last_known_location(self, object_name):
        """Retrieves the last known location of an object."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, last_seen, x, y, room, bounding_box FROM objects WHERE name = ?", (object_name,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        cursor.execute("SELECT timestamp, x, y, room, bounding_box FROM object_history WHERE object_name = ? ORDER BY id ASC", (object_name,))
        hist_rows = cursor.fetchall()
        history = []
        for h in hist_rows:
            history.append({
                "timestamp": h["timestamp"],
                "x": h["x"],
                "y": h["y"],
                "room": h["room"],
                "bounding_box": json.loads(h["bounding_box"]) if h["bounding_box"] else None
            })
            
        conn.close()
        
        return {
            "last_seen": row["last_seen"],
            "x": row["x"],
            "y": row["y"],
            "room": row["room"],
            "bounding_box": json.loads(row["bounding_box"]) if row["bounding_box"] else None,
            "history": history
        }

    def get_object_history(self, object_name):
        """Retrieves the history of detection events for an object."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, x, y, room, bounding_box FROM object_history WHERE object_name = ? ORDER BY id ASC", (object_name,))
        rows = cursor.fetchall()
        
        history = []
        for r in rows:
            history.append({
                "timestamp": r["timestamp"],
                "x": r["x"],
                "y": r["y"],
                "room": r["room"],
                "bounding_box": json.loads(r["bounding_box"]) if r["bounding_box"] else None
            })
        conn.close()
        return history

    def set_current_room(self, room_name):
        """Sets the active room location of the device."""
        self._set_system_state("current_room", room_name)
        return True

    def get_current_room(self):
        """Gets the active room location of the device."""
        return self._get_system_state("current_room", "Living Room")

    def clear(self):
        """Clears all database contents (useful for testing)."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM system_state")
            cursor.execute("DELETE FROM identities")
            cursor.execute("DELETE FROM face_embeddings")
            cursor.execute("DELETE FROM identity_evidence")
            cursor.execute("DELETE FROM objects")
            cursor.execute("DELETE FROM object_history")
            
            cursor.execute("INSERT INTO system_state (key, value) VALUES ('next_anon_index', '1')")
            cursor.execute("INSERT INTO system_state (key, value) VALUES ('current_room', 'Living Room')")
            
            conn.commit()
            conn.close()

    # --- Evidence Accumulation logic ---

    def add_evidence(self, identity_id, name, relationship=None, raw_transcript=None):
        """
        Adds audio context evidence for an identity.
        Recalculates confidence score based on cumulative evidence.
        If confidence >= 80% (0.80), binds the identity.
        Returns:
            dict: The updated candidate info: { "name": str, "relationship": str/None, "confidence": float, "is_confirmed": bool }
        """
        if not identity_id or not name:
            return None

        name = name.strip().capitalize()
        if relationship:
            relationship = relationship.strip().capitalize()

        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if identity is already confirmed. Never overwrite a confirmed profile!
            cursor.execute("SELECT status, display_name, relationship FROM identities WHERE identity_id = ?", (identity_id,))
            id_row = cursor.fetchone()
            if not id_row:
                conn.close()
                return None
            
            if id_row["status"] == "confirmed":
                conn.close()
                return {
                    "name": id_row["display_name"],
                    "relationship": id_row["relationship"],
                    "confidence": 1.0,
                    "is_confirmed": True
                }
            
            cursor.execute(
                "SELECT count, confidence FROM identity_evidence WHERE identity_id = ? AND heard_name = ?",
                (identity_id, name)
            )
            row = cursor.fetchone()
            
            new_count = 1
            final_rel = relationship
            
            if row:
                new_count = row["count"] + 1
                cursor.execute(
                    "SELECT heard_relationship FROM identity_evidence WHERE identity_id = ? AND heard_name = ?",
                    (identity_id, name)
                )
                prev_rel_row = cursor.fetchone()
                final_rel = relationship or (prev_rel_row[0] if prev_rel_row else None)
                
                cursor.execute(
                    "UPDATE identity_evidence SET count = ?, heard_relationship = ?, updated_at = ? WHERE identity_id = ? AND heard_name = ?",
                    (new_count, final_rel, datetime.now().isoformat(), identity_id, name)
                )
            else:
                now_str = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO identity_evidence (identity_id, heard_name, heard_relationship, count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (identity_id, name, final_rel, 1, now_str, now_str)
                )

            if final_rel:
                if new_count == 1:
                    confidence = 0.90
                else:
                    confidence = 0.85
            else:
                confidence = 0.40
                if raw_transcript and raw_transcript.strip().lower() == name.lower():
                    confidence = 0.60
                
                if new_count == 2:
                    confidence = max(confidence, 0.70)
                elif new_count >= 3:
                    confidence = max(confidence, 0.80)

            cursor.execute(
                "UPDATE identity_evidence SET confidence = ? WHERE identity_id = ? AND heard_name = ?",
                (confidence, identity_id, name)
            )
            
            # Fetch and update identities table attributes
            cursor.execute("SELECT evidence_history FROM identities WHERE identity_id = ?", (identity_id,))
            hist_row = cursor.fetchone()
            ev_history = []
            if hist_row and hist_row[0]:
                try:
                    ev_history = json.loads(hist_row[0])
                except Exception:
                    pass
            
            ev_history.append({
                "timestamp": datetime.now().isoformat(),
                "heard_name": name,
                "heard_relationship": final_rel,
                "raw_transcript": raw_transcript,
                "confidence": confidence,
                "count": new_count
            })
            
            is_confirmed = (confidence >= 0.80)
            status = "confirmed" if is_confirmed else "unconfirmed"
            now_str = datetime.now().isoformat()
            
            cursor.execute(
                """UPDATE identities SET 
                   display_name = CASE WHEN ? = 'confirmed' THEN ? ELSE display_name END,
                   relationship = CASE WHEN ? = 'confirmed' THEN ? ELSE relationship END,
                   status = ?,
                   candidate_name = ?,
                   candidate_relationship = ?,
                   confidence = ?,
                   last_seen = ?,
                   evidence_history = ?
                   WHERE identity_id = ?""",
                (status, name, status, final_rel, status, name, final_rel, confidence, now_str, json.dumps(ev_history), identity_id)
            )
                
            conn.commit()
            conn.close()
            
            return {
                "name": name,
                "relationship": final_rel,
                "confidence": confidence,
                "is_confirmed": is_confirmed
            }

    def get_candidates(self, identity_id):
        """
        Retrieves all candidate identities recorded for an identity_id, sorted by confidence descending.
        Returns:
            list: List of dicts: [ { "name": str, "relationship": str/None, "count": int, "confidence": float } ]
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT heard_name, heard_relationship, count, confidence FROM identity_evidence WHERE identity_id = ? ORDER BY confidence DESC",
            (identity_id,)
        )
        rows = cursor.fetchall()
        
        candidates = []
        for r in rows:
            candidates.append({
                "name": r["heard_name"],
                "relationship": r["heard_relationship"],
                "count": r["count"],
                "confidence": r["confidence"]
            })
            
        conn.close()
        return candidates
