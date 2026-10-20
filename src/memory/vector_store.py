"""
FAISS-backed face-embedding store.

Persistence model
-----------------
The JSON mapping file (identity ids + raw embeddings) is the authoritative
record. The FAISS index is a derived search structure that is always rebuilt
from that record on load, so the two cannot silently diverge. The ``.index``
file is still written for compatibility with older tooling.

A store constructed without paths is purely in-memory and never touches the
filesystem. Each ``MemoraDatabase`` passes paths derived from its own database
file, so test and demo databases can no longer read, write, or delete the
embeddings belonging to a different database.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Optional

import faiss
import numpy as np

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 128


class VectorStoreError(RuntimeError):
    """Raised when an embedding cannot be stored or persisted."""


class FaissVectorStore:
    """
    Manages face embeddings using FAISS for fast similarity search.
    """

    def __init__(self, index_path: Optional[str] = None, mapping_path: Optional[str] = None,
                 legacy_paths: Optional[tuple[str, str]] = None):
        self._lock = threading.Lock()
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.persistent = bool(index_path and mapping_path)
        self.embedding_dim = EMBEDDING_DIM

        # FAISS integer id -> identity id
        self.id_mapping: dict[int, str] = {}
        # FAISS integer id -> raw embedding (authoritative copy, used for EMA and rebuilds)
        self.embeddings_cache: dict[int, np.ndarray] = {}
        self.next_id = 0

        # Diagnostics surfaced through MemoraDatabase.check_integrity()
        self.load_error: Optional[str] = None
        self.last_save_error: Optional[str] = None
        self.loaded_from: Optional[str] = None

        self.index = self._new_index()
        if self.persistent:
            self._load(legacy_paths)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _new_index(self):
        return faiss.IndexIDMap2(faiss.IndexFlatL2(self.embedding_dim))

    def _load(self, legacy_paths: Optional[tuple[str, str]]) -> None:
        source = self.mapping_path
        if not os.path.exists(source) and legacy_paths and os.path.exists(legacy_paths[1]):
            # Adopt embeddings written by older versions next to the default DB.
            # The legacy files are read, never modified or deleted.
            source = legacy_paths[1]
        if not os.path.exists(source):
            return

        try:
            with open(source, "r") as f:
                data = json.load(f)
            id_mapping = {int(k): str(v) for k, v in data.get("id_mapping", {}).items()}
            cache = {}
            for k, v in data.get("embeddings_cache", {}).items():
                vec = np.asarray(v, dtype=np.float32).reshape(-1)
                if vec.shape[0] != self.embedding_dim:
                    raise ValueError(f"embedding {k} has dimension {vec.shape[0]}, expected {self.embedding_dim}")
                cache[int(k)] = vec
            missing = sorted(set(id_mapping) - set(cache))
            if missing:
                raise ValueError(f"mapping references {len(missing)} embeddings that are not stored")
            next_id = int(data.get("next_id", (max(id_mapping) + 1) if id_mapping else 0))
        except Exception as e:
            self.load_error = f"Could not read face embeddings from {source}: {e}"
            logger.error(self.load_error)
            if source == self.mapping_path:
                self._quarantine()
            return

        self.id_mapping = id_mapping
        self.embeddings_cache = cache
        self.next_id = max(next_id, (max(cache) + 1) if cache else 0)
        self.loaded_from = source
        self._rebuild_index()

    def _quarantine(self) -> None:
        """Move unreadable files aside so a later save cannot overwrite them."""
        suffix = time.strftime(".corrupt-%Y%m%d%H%M%S")
        for path in (self.mapping_path, self.index_path):
            if path and os.path.exists(path):
                try:
                    os.replace(path, path + suffix)
                    logger.error("Quarantined unreadable vector store file: %s", path + suffix)
                except OSError as e:
                    logger.error("Failed to quarantine %s: %s", path, e)

    def _save_index(self) -> bool:
        """Atomically persist the mapping and index. Returns True on success."""
        if not self.persistent:
            return True
        try:
            directory = os.path.dirname(os.path.abspath(self.mapping_path))
            os.makedirs(directory, exist_ok=True)
            payload = {
                "id_mapping": {str(k): v for k, v in self.id_mapping.items()},
                "embeddings_cache": {str(k): v.tolist() for k, v in self.embeddings_cache.items()},
                "next_id": self.next_id,
                "embedding_dim": self.embedding_dim,
            }
            tmp_map = self.mapping_path + ".tmp"
            with open(tmp_map, "w") as f:
                json.dump(payload, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_map, self.mapping_path)

            tmp_idx = self.index_path + ".tmp"
            faiss.write_index(self.index, tmp_idx)
            os.replace(tmp_idx, self.index_path)
            self.last_save_error = None
            return True
        except Exception as e:
            self.last_save_error = f"Failed to persist face embeddings: {e}"
            logger.error(self.last_save_error)
            return False

    def _rebuild_index(self) -> None:
        self.index = self._new_index()
        if not self.embeddings_cache:
            return
        ids = np.array(sorted(self.embeddings_cache), dtype=np.int64)
        vectors = np.stack([self.embeddings_cache[i] for i in ids]).astype(np.float32)
        self.index.add_with_ids(vectors, ids)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def _validate(self, embedding) -> np.ndarray:
        vec = np.asarray(embedding, dtype=np.float32).reshape(-1)
        if vec.shape[0] != self.embedding_dim:
            raise VectorStoreError(f"Embedding has dimension {vec.shape[0]}, expected {self.embedding_dim}.")
        if not np.all(np.isfinite(vec)):
            raise VectorStoreError("Embedding contains non-finite values.")
        return vec

    def add_embedding(self, identity_id: str, embedding: np.ndarray) -> int:
        """
        Adds a new embedding and maps it to identity_id. Returns the faiss_id.

        Raises VectorStoreError if the embedding is invalid or cannot be persisted;
        in that case the in-memory state is rolled back.
        """
        vec = self._validate(embedding)
        with self._lock:
            faiss_id = self.next_id
            self.id_mapping[faiss_id] = identity_id
            self.embeddings_cache[faiss_id] = vec
            self.next_id += 1
            self.index.add_with_ids(vec.reshape(1, -1), np.array([faiss_id], dtype=np.int64))

            if not self._save_index():
                del self.id_mapping[faiss_id]
                del self.embeddings_cache[faiss_id]
                self.next_id -= 1
                self._rebuild_index()
                raise VectorStoreError(self.last_save_error or "Failed to persist face embedding.")
            return faiss_id

    def update_embedding_ema(self, faiss_id: int, new_embedding: np.ndarray, alpha: float = 0.1):
        """
        Updates an existing embedding using an exponential moving average.
        """
        vec = self._validate(new_embedding)
        with self._lock:
            if faiss_id not in self.embeddings_cache:
                return
            stored = self.embeddings_cache[faiss_id]
            self.embeddings_cache[faiss_id] = (alpha * vec + (1 - alpha) * stored).astype(np.float32)
            self._rebuild_index()
            self._save_index()

    def remove_identity(self, identity_id: str) -> int:
        """Delete every embedding belonging to identity_id. Returns the number removed."""
        with self._lock:
            doomed = [fid for fid, iid in self.id_mapping.items() if iid == identity_id]
            for fid in doomed:
                del self.id_mapping[fid]
                self.embeddings_cache.pop(fid, None)
            if doomed:
                self._rebuild_index()
                if not self._save_index():
                    raise VectorStoreError(self.last_save_error or "Failed to persist embedding deletion.")
            return len(doomed)

    def clear(self):
        """Remove all embeddings held by this store (and only this store's files)."""
        with self._lock:
            self.index = self._new_index()
            self.id_mapping.clear()
            self.embeddings_cache.clear()
            self.next_id = 0
            if self.persistent:
                for path in (self.index_path, self.mapping_path):
                    if os.path.exists(path):
                        os.remove(path)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_match(self, query_embedding: np.ndarray, tolerance: float):
        """
        Returns (identity_id, faiss_id, distance) for the nearest embedding whose
        L2 distance is below tolerance, else (None, None, None).
        """
        query = self._validate(query_embedding).reshape(1, -1)
        with self._lock:
            if self.index.ntotal == 0:
                return None, None, None
            distances, indices = self.index.search(query, 1)
            if len(distances) == 0 or len(distances[0]) == 0 or indices[0][0] < 0:
                return None, None, None
            dist = float(np.sqrt(distances[0][0]))
            faiss_id = int(indices[0][0])
            if dist < tolerance:
                return self.id_mapping.get(faiss_id), faiss_id, dist
            return None, None, None

    def get_embeddings_for_identity(self, identity_id: str):
        """
        Returns a list of embeddings associated with a given identity_id.
        """
        with self._lock:
            return [self.embeddings_cache[fid] for fid, iid in self.id_mapping.items()
                    if iid == identity_id and fid in self.embeddings_cache]

    def identity_ids(self) -> set[str]:
        with self._lock:
            return set(self.id_mapping.values())

    def __len__(self) -> int:
        return len(self.embeddings_cache)
