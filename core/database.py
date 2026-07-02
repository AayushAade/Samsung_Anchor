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
                # The file is not a valid database (likely the old JSON file).
                # We should remove or rename it to avoid crashing!
                print(f"[Database Warning] Invalid database file detected at {self.db_path} (likely old JSON database). Replacing with new SQLite database.")
                try:
                    conn.close()
                except Exception:
                    pass
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
            
            # system_state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # identities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS identities (
                    face_id TEXT PRIMARY KEY,
                    name TEXT,
                    relationship TEXT,
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # face_embeddings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS face_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    face_id TEXT,
                    embedding TEXT,
                    FOREIGN KEY(face_id) REFERENCES identities(face_id) ON DELETE CASCADE
                )
            """)
            
            # identity_evidence table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS identity_evidence (
                    face_id TEXT,
                    heard_name TEXT,
                    heard_relationship TEXT,
                    count INTEGER DEFAULT 1,
                    confidence REAL DEFAULT 0.0,
                    created_at TEXT,
                    updated_at TEXT,
                    PRIMARY KEY(face_id, heard_name),
                    FOREIGN KEY(face_id) REFERENCES identities(face_id) ON DELETE CASCADE
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
        """No-op for SQLite (schema initialized at startup)."""
        pass

    def save(self):
        """No-op for SQLite (writes commit instantly)."""
        pass

    def find_match(self, query_embedding, tolerance=None):
        """
        Compares query_embedding (128D list/array) against all stored identities.
        Returns (face_id, identity_dict, distance) if a match is found under the tolerance,
        otherwise returns (None, None, None).
        """
        if tolerance is None:
            tolerance = settings.FACE_TOLERANCE

        query_vector = np.array(query_embedding)
        best_match_id = None
        best_distance = float("inf")

        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT face_id, embedding FROM face_embeddings")
            rows = cursor.fetchall()
            
            for r in rows:
                face_id = r["face_id"]
                stored_embedding = json.loads(r["embedding"])
                stored_vector = np.array(stored_embedding)
                distance = np.linalg.norm(query_vector - stored_vector)
                
                # Fetch name for logging comparison
                cursor2 = conn.cursor()
                cursor2.execute("SELECT name FROM identities WHERE face_id = ?", (face_id,))
                name_row = cursor2.fetchone()
                name_str = name_row[0] if (name_row and name_row[0]) else face_id
                
                print(f"Comparing with {name_str}")
                print(f"Distance = {distance:.4f}")
                
                if distance < tolerance and distance < best_distance:
                    best_distance = distance
                    best_match_id = face_id
            
            conn.close()
            
            if best_match_id is not None:
                return best_match_id, self.get_identity(best_match_id), best_distance

        return None, None, None

    def register_anonymous(self, embedding):
        """
        Registers a new anonymous identity with the given embedding vector.
        Returns the generated face_id.
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
                "INSERT INTO identities (face_id, name, relationship, confidence, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (anon_id, None, None, 0.0, now_str, now_str)
            )
            
            embedding_json = json.dumps(list(embedding))
            cursor.execute(
                "INSERT INTO face_embeddings (face_id, embedding) VALUES (?, ?)",
                (anon_id, embedding_json)
            )
            
            conn.commit()
            conn.close()
            return anon_id

    def add_embedding_to_identity(self, face_id, embedding):
        """Adds a new embedding vector to an existing identity's database profile (for model reinforcement)."""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM identities WHERE face_id = ?", (face_id,))
            if not cursor.fetchone():
                conn.close()
                return False
                
            now_str = datetime.now().isoformat()
            cursor.execute("UPDATE identities SET updated_at = ? WHERE face_id = ?", (now_str, face_id))
            
            embedding_json = json.dumps(list(embedding))
            cursor.execute(
                "INSERT INTO face_embeddings (face_id, embedding) VALUES (?, ?)",
                (face_id, embedding_json)
            )
            
            conn.commit()
            conn.close()
            return True

    def bind_name(self, face_id, name, relationship=None):
        """
        Binds a name and optional relationship to an existing anonymous or known face_id.
        Sets confidence to 1.0 (confirmed).
        """
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM identities WHERE face_id = ?", (face_id,))
            if not cursor.fetchone():
                conn.close()
                return False
                
            now_str = datetime.now().isoformat()
            cursor.execute(
                "UPDATE identities SET name = ?, relationship = ?, confidence = 1.0, updated_at = ? WHERE face_id = ?",
                (name, relationship, now_str, face_id)
            )
                
            conn.commit()
            conn.close()
            return True

    def get_identity(self, face_id):
        """Retrieves identity information for a given face_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, relationship, confidence, created_at, updated_at FROM identities WHERE face_id = ?", (face_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        cursor.execute("SELECT embedding FROM face_embeddings WHERE face_id = ?", (face_id,))
        emb_rows = cursor.fetchall()
        embeddings = [json.loads(r["embedding"]) for r in emb_rows]
        
        conn.close()
        
        return {
            "name": row["name"],
            "relationship": row["relationship"],
            "confidence": row["confidence"],
            "embeddings": embeddings,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

    def get_all_identities(self):
        """Returns all identity records."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT face_id FROM identities")
        rows = cursor.fetchall()
        
        identities_dict = {}
        for r in rows:
            face_id = r["face_id"]
            identities_dict[face_id] = self.get_identity(face_id)
            
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

    def add_evidence(self, face_id, name, relationship=None):
        """
        Adds audio context evidence for an identity.
        Recalculates confidence score based on cumulative evidence.
        If confidence >= 80% (0.80), binds the identity.
        Returns:
            dict: The updated candidate info: { "name": str, "relationship": str/None, "confidence": float, "is_confirmed": bool }
        """
        if not face_id or not name:
            return None

        name = name.strip().capitalize()
        if relationship:
            relationship = relationship.strip().capitalize()

        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM identities WHERE face_id = ?", (face_id,))
            if not cursor.fetchone():
                conn.close()
                return None
            
            cursor.execute(
                "SELECT count, heard_relationship FROM identity_evidence WHERE face_id = ? AND heard_name = ?",
                (face_id, name)
            )
            row = cursor.fetchone()
            
            new_count = 1
            final_rel = relationship
            
            if row:
                new_count = row["count"] + 1
                final_rel = relationship or row["heard_relationship"]
                
                cursor.execute(
                    "UPDATE identity_evidence SET count = ?, heard_relationship = ?, updated_at = ? WHERE face_id = ? AND heard_name = ?",
                    (new_count, final_rel, datetime.now().isoformat(), face_id, name)
                )
            else:
                now_str = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO identity_evidence (face_id, heard_name, heard_relationship, count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (face_id, name, final_rel, 1, now_str, now_str)
                )

            # Confidence logic:
            # - count = 1, no relationship: 40% (0.40)
            # - count = 2, no relationship: 70% (0.70)
            # - count >= 3, no relationship: 80% (0.80)
            # - count = 1, relationship: 90% (0.90)
            # - count >= 2, relationship: 85% (0.85) (to match demo requirement of 85%)
            if final_rel:
                if new_count == 1:
                    confidence = 0.90
                else:
                    confidence = 0.85
            else:
                if new_count == 1:
                    confidence = 0.40
                elif new_count == 2:
                    confidence = 0.70
                else:
                    confidence = 0.80

            cursor.execute(
                "UPDATE identity_evidence SET confidence = ? WHERE face_id = ? AND heard_name = ?",
                (confidence, face_id, name)
            )
            
            is_confirmed = False
            # Check if this candidate's confidence is >= 0.80.
            # If so, bind the identity
            if confidence >= 0.80:
                now_str = datetime.now().isoformat()
                cursor.execute(
                    "UPDATE identities SET name = ?, relationship = ?, confidence = ?, updated_at = ? WHERE face_id = ?",
                    (name, final_rel, confidence, now_str, face_id)
                )
                is_confirmed = True
                
            conn.commit()
            conn.close()
            
            return {
                "name": name,
                "relationship": final_rel,
                "confidence": confidence,
                "is_confirmed": is_confirmed
            }

    def get_candidates(self, face_id):
        """
        Retrieves all candidate identities recorded for a face_id, sorted by confidence descending.
        Returns:
            list: List of dicts: [ { "name": str, "relationship": str/None, "count": int, "confidence": float } ]
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT heard_name, heard_relationship, count, confidence FROM identity_evidence WHERE face_id = ? ORDER BY confidence DESC",
            (face_id,)
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
