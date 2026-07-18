import os
import json
import faiss
import numpy as np
from config import settings

class FaissVectorStore:
    """
    Manages Face Embeddings using FAISS for fast similarity search.
    Stores embeddings locally alongside SQLite.
    """
    def __init__(self, index_path=None, mapping_path=None):
        self.index_path = index_path or os.path.join(os.path.dirname(settings.DB_PATH), "face_embeddings.index")
        self.mapping_path = mapping_path or os.path.join(os.path.dirname(settings.DB_PATH), "face_mapping.json")
        self.embedding_dim = 128
        
        # Mapping from FAISS integer ID (0 to N) to String Identity ID
        self.id_mapping = {}
        # Mapping from FAISS integer ID to the raw embedding (for EMA updates)
        self.embeddings_cache = {}
        self.next_id = 0
        
        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.mapping_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.mapping_path, "r") as f:
                data = json.load(f)
                # Convert string keys back to int for id_mapping
                self.id_mapping = {int(k): v for k, v in data.get("id_mapping", {}).items()}
                self.next_id = data.get("next_id", 0)
                # Convert list back to numpy arrays
                self.embeddings_cache = {int(k): np.array(v) for k, v in data.get("embeddings_cache", {}).items()}
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)

    def _save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.mapping_path, "w") as f:
            # Convert numpy arrays to lists for JSON serialization
            cache_list = {k: v.tolist() for k, v in self.embeddings_cache.items()}
            json.dump({
                "id_mapping": self.id_mapping,
                "embeddings_cache": cache_list,
                "next_id": self.next_id
            }, f)

    def add_embedding(self, identity_id: str, embedding: np.ndarray) -> int:
        """
        Adds a new embedding to the FAISS index and maps it to identity_id.
        Returns the faiss_id.
        """
        embedding = np.array(embedding, dtype=np.float32).reshape(1, -1)
        self.index.add(embedding)
        
        faiss_id = self.next_id
        self.id_mapping[faiss_id] = identity_id
        self.embeddings_cache[faiss_id] = embedding[0]
        self.next_id += 1
        
        self._save_index()
        return faiss_id

    def update_embedding_ema(self, faiss_id: int, new_embedding: np.ndarray, alpha: float = 0.1):
        """
        Updates an existing embedding using Exponential Moving Average.
        Since FAISS IndexFlatL2 doesn't support inplace updates easily,
        we rebuild the index. For a small number of faces (e.g. edge), this is extremely fast.
        """
        if faiss_id not in self.embeddings_cache:
            return

        stored_vector = self.embeddings_cache[faiss_id]
        new_vector = np.array(new_embedding, dtype=np.float32)
        updated_vector = alpha * new_vector + (1 - alpha) * stored_vector
        
        self.embeddings_cache[faiss_id] = updated_vector
        
        # Rebuild FAISS index
        self._rebuild_index()
        self._save_index()

    def _rebuild_index(self):
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        if not self.embeddings_cache:
            return
            
        vectors = []
        for i in range(self.next_id):
            if i in self.embeddings_cache:
                vectors.append(self.embeddings_cache[i])
            else:
                # Should not happen if data is consistent, but safeguard
                vectors.append(np.zeros(self.embedding_dim, dtype=np.float32))
                
        if vectors:
            self.index.add(np.array(vectors, dtype=np.float32))

    def find_match(self, query_embedding: np.ndarray, tolerance: float):
        """
        Returns (identity_id, faiss_id, distance) if found, else (None, None, None).
        Tolerance represents the max L2 distance squared in FAISS for FlatL2,
        but since the old code used L2 norm directly, we square the tolerance if it's not squared.
        Actually, we'll just take sqrt of FAISS distance to match old behavior.
        """
        if self.index.ntotal == 0:
            return None, None, None

        query = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
        # Search top 1 nearest neighbor
        distances, indices = self.index.search(query, 1)
        
        if len(distances) == 0 or len(distances[0]) == 0:
            return None, None, None

        dist_sq = distances[0][0]
        dist = np.sqrt(dist_sq)
        faiss_id = indices[0][0]
        
        if dist < tolerance:
            identity_id = self.id_mapping.get(faiss_id)
            return identity_id, faiss_id, dist
            
        return None, None, None
    
    def get_embeddings_for_identity(self, identity_id: str):
        """
        Returns a list of embeddings associated with a given identity_id.
        """
        embeddings = []
        for fid, iid in self.id_mapping.items():
            if iid == identity_id and fid in self.embeddings_cache:
                embeddings.append(self.embeddings_cache[fid])
        return embeddings

    def clear(self):
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.id_mapping.clear()
        self.embeddings_cache.clear()
        self.next_id = 0
        if os.path.exists(self.index_path):
            os.remove(self.index_path)
        if os.path.exists(self.mapping_path):
            os.remove(self.mapping_path)
