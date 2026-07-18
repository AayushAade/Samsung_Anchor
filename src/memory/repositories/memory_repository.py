from sqlalchemy.orm import Session
from src.memory.models import RelevantMemoryModel, EpisodeModel, SemanticNodeModel
from src.cognition.memory_models import RelevantMemory, MemoryType, MemoryImportance
from src.cognition.memory_query import MemoryQuery
from datetime import datetime
import uuid

class DatabaseMemoryRepository:
    """
    SQLAlchemy backed repository for retrieving all relevant memories.
    It queries both explicit long-term extracted memories (Semantic)
    and raw episodic experiences (Episodic).
    """
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def save(self, memory: RelevantMemory) -> None:
        with self.session_factory() as session:
            db_memory = session.query(RelevantMemoryModel).filter_by(memory_id=memory.memory_id).first()
            if not db_memory:
                db_memory = RelevantMemoryModel(memory_id=memory.memory_id)
                session.add(db_memory)
                
            db_memory.memory_type = memory.memory_type.value
            db_memory.importance = memory.importance.value
            db_memory.title = memory.title
            db_memory.summary = memory.summary
            db_memory.person = memory.person
            db_memory.location = memory.location
            db_memory.timestamp = memory.timestamp.isoformat() if isinstance(memory.timestamp, datetime) else str(memory.timestamp)
            db_memory.commitments = memory.commitments
            db_memory.tags = memory.tags
            
            session.commit()

    def find(self, query: MemoryQuery) -> list[RelevantMemory]:
        results = []
        with self.session_factory() as session:
            # 1. Fetch Explicit Memories
            q_mem = session.query(RelevantMemoryModel)
            if query.face_id is not None:
                q_mem = q_mem.filter(RelevantMemoryModel.person == query.face_id)
            for m in q_mem.all():
                results.append(self._to_domain(m))

            # 2. Fetch Semantic Nodes (Knowledge Graph)
            q_sem = session.query(SemanticNodeModel)
            if query.face_id is not None:
                # Match subject to face_id (case insensitive for safety)
                q_sem = q_sem.filter(SemanticNodeModel.subject.ilike(f"%{query.face_id}%"))
            for node in q_sem.all():
                try:
                    ts = datetime.fromisoformat(node.last_reinforced)
                except Exception:
                    ts = datetime.now()
                
                rm = RelevantMemory(
                    memory_id=f"sem_{node.id}",
                    memory_type=MemoryType.SEMANTIC,
                    importance=MemoryImportance(node.importance),
                    title=f"Knowledge about {node.subject}",
                    summary=f"{node.subject} {node.predicate} {node.object_val} (Confidence: {node.confidence:.2f})",
                    person=node.subject,
                    location=None,
                    timestamp=ts,
                    historical_usefulness=node.historical_usefulness,
                    confidence=node.confidence
                )
                results.append(rm)

            # 3. Fetch Episodes and convert to RelevantMemory dynamically
            q_ep = session.query(EpisodeModel)
            if query.face_id is not None:
                # Assuming person column stores the identity ID
                q_ep = q_ep.filter(EpisodeModel.person == query.face_id)
                
            for ep in q_ep.all():
                try:
                    ts = datetime.fromisoformat(ep.timestamp) if ep.timestamp else datetime.now()
                except Exception:
                    ts = datetime.now()
                
                rm = RelevantMemory(
                    memory_id=f"ep_{ep.id}",
                    memory_type=MemoryType.EPISODIC,
                    importance=MemoryImportance.NORMAL,
                    title=f"Interaction with {ep.person}",
                    summary=ep.summary,
                    person=ep.person,
                    location=ep.location,
                    timestamp=ts,
                    commitments=list(ep.commitments) if ep.commitments else [],
                    tags=list(ep.tags) if ep.tags else []
                )
                results.append(rm)

        return results

    def clear(self) -> None:
        with self.session_factory() as session:
            session.query(RelevantMemoryModel).delete()
            session.commit()
            
    def _to_domain(self, db_model: RelevantMemoryModel) -> RelevantMemory:
        try:
            ts = datetime.fromisoformat(db_model.timestamp) if db_model.timestamp else None
        except Exception:
            ts = None
            
        return RelevantMemory(
            memory_id=db_model.memory_id,
            memory_type=MemoryType(db_model.memory_type),
            importance=MemoryImportance(db_model.importance),
            title=db_model.title or "",
            summary=db_model.summary or "",
            person=db_model.person,
            location=db_model.location,
            timestamp=ts,
            commitments=list(db_model.commitments) if db_model.commitments else [],
            tags=list(db_model.tags) if db_model.tags else []
        )
