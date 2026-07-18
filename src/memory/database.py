import os
import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from src.memory.models import Base, SystemState, IdentityEvidence
from src.memory.vector_store import FaissVectorStore
from src.memory.repositories.identity_repository import IdentityRepository
from src.memory.repositories.object_repository import ObjectRepository
from src.memory.repositories.episode_repository import DatabaseEpisodeRepository
from src.memory.repositories.memory_repository import DatabaseMemoryRepository

class MemoraDatabase:
    """
    Facade for the new SQLAlchemy + FAISS architecture.
    Maintains the same public API as the old SQLite-only implementation
    to ensure backward compatibility with the rest of the application.
    """
    def __init__(self, db_path=None):
        # We append _v2 to start fresh, avoiding schema conflicts with the old DB
        base_path = db_path or settings.DB_PATH
        if not base_path.endswith('_v2.sqlite'):
            self.db_path = base_path.replace('.sqlite', '_v2.sqlite')
        else:
            self.db_path = base_path

        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        self.engine = create_engine(f"sqlite:///{self.db_path}", connect_args={"check_same_thread": False, "timeout": 30.0})
        Base.metadata.create_all(self.engine)
        
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.lock = threading.Lock()

        # Initialize Sub-Repositories
        self.vector_store = FaissVectorStore()
        self.identity_repo = IdentityRepository(self.SessionFactory)
        self.object_repo = ObjectRepository(self.SessionFactory)
        self.episode_repo = DatabaseEpisodeRepository(self.SessionFactory)
        self.memory_repo = DatabaseMemoryRepository(self.SessionFactory)

        self._init_system_state()

    def _init_system_state(self):
        with self.SessionFactory() as session:
            if not session.query(SystemState).filter_by(key="next_anon_index").first():
                session.add(SystemState(key="next_anon_index", value="1"))
            if not session.query(SystemState).filter_by(key="current_room").first():
                session.add(SystemState(key="current_room", value="Living Room"))
            session.commit()

    def _get_system_state(self, key, default=None):
        with self.SessionFactory() as session:
            state = session.query(SystemState).filter_by(key=key).first()
            return state.value if state else default

    def _set_system_state(self, key, value):
        with self.SessionFactory() as session:
            state = session.query(SystemState).filter_by(key=key).first()
            if state:
                state.value = str(value)
            else:
                session.add(SystemState(key=key, value=str(value)))
            session.commit()

    @property
    def data(self):
        return {
            "identities": self.get_all_identities(),
            "next_anon_index": int(self._get_system_state("next_anon_index", 1)),
            "objects": self.object_repo.get_all_objects(),
            "current_room": self._get_system_state("current_room", "Living Room")
        }

    def load(self):
        pass

    def save(self):
        pass

    def find_match(self, query_embedding, tolerance=None):
        if tolerance is None:
            tolerance = settings.FACE_TOLERANCE

        with self.lock:
            identity_id, faiss_id, distance = self.vector_store.find_match(query_embedding, tolerance)
            
            if identity_id is not None:
                identity_info = self.identity_repo.get_by_id(identity_id)
                if identity_info:
                    identity_info["embedding_row_id"] = faiss_id
                    identity_info["embeddings"] = self.vector_store.get_embeddings_for_identity(identity_id)
                return identity_id, identity_info, distance
                
        return None, None, None

    def register_anonymous(self, embedding):
        with self.lock:
            anon_index = int(self._get_system_state("next_anon_index", "1"))
            anon_id = f"Anonymous_ID_{anon_index}"
            
            self._set_system_state("next_anon_index", str(anon_index + 1))
            self.identity_repo.register_anonymous(anon_id)
            self.vector_store.add_embedding(anon_id, embedding)
            
            return anon_id

    def add_embedding_to_identity(self, identity_id, embedding):
        with self.lock:
            identity = self.identity_repo.get_by_id(identity_id)
            if not identity:
                return False
                
            self.vector_store.add_embedding(identity_id, embedding)
            self.identity_repo.increment_times_seen(identity_id)
            return True

    def update_embedding_ema(self, embedding_id, new_embedding, alpha=0.1):
        with self.lock:
            if embedding_id is not None:
                self.vector_store.update_embedding_ema(embedding_id, new_embedding, alpha)

    def increment_times_seen(self, identity_id):
        with self.lock:
            self.identity_repo.increment_times_seen(identity_id)

    def bind_name(self, identity_id, name, relationship=None):
        with self.lock:
            # We use add_evidence logic as a shortcut, or manually update
            with self.SessionFactory() as session:
                from src.memory.models import Identity
                identity = session.query(Identity).filter_by(identity_id=identity_id).first()
                if not identity:
                    return False
                identity.display_name = name
                identity.relationship = relationship
                identity.status = "confirmed"
                identity.confidence = 1.0
                session.commit()
            return True

    def get_identity(self, identity_id):
        identity_info = self.identity_repo.get_by_id(identity_id)
        if identity_info:
            identity_info["embeddings"] = self.vector_store.get_embeddings_for_identity(identity_id)
        return identity_info

    def get_all_identities(self):
        identities_list = self.identity_repo.get_all()
        result = {}
        for info in identities_list:
            info["embeddings"] = self.vector_store.get_embeddings_for_identity(info["identity_id"])
            result[info["identity_id"]] = info
        return result

    def log_object(self, object_name, x, y, room, bounding_box=None):
        with self.lock:
            return self.object_repo.log_object(object_name, x, y, room, bounding_box)

    def get_last_known_location(self, object_name):
        return self.object_repo.get_last_known_location(object_name)

    def get_object_history(self, object_name):
        loc = self.object_repo.get_last_known_location(object_name)
        return loc["history"] if loc else []

    def set_current_room(self, room_name):
        self._set_system_state("current_room", room_name)
        return True

    def get_current_room(self):
        return self._get_system_state("current_room", "Living Room")

    def clear(self):
        with self.lock:
            Base.metadata.drop_all(self.engine)
            Base.metadata.create_all(self.engine)
            self.vector_store.clear()
            self._init_system_state()

    def add_evidence(self, identity_id, name, relationship=None, raw_transcript=None):
        with self.lock:
            return self.identity_repo.add_evidence(identity_id, name, relationship, raw_transcript)

    def get_candidates(self, identity_id):
        with self.SessionFactory() as session:
            evidences = session.query(IdentityEvidence).filter_by(identity_id=identity_id).order_by(IdentityEvidence.confidence.desc()).all()
            return [{
                "name": ev.heard_name,
                "relationship": ev.heard_relationship,
                "count": ev.count,
                "confidence": ev.confidence
            } for ev in evidences]
