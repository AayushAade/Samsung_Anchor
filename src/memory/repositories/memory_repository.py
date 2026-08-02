from typing import Optional, Any, List
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

    def find(self, query: Optional[Any] = None, tags: Optional[list[str]] = None) -> list[RelevantMemory]:
        results = []
        with self.session_factory() as session:
            # 1. Fetch Explicit Memories
            q_mem = session.query(RelevantMemoryModel)
            if query is not None and hasattr(query, "face_id") and query.face_id is not None:
                clean_id = query.face_id.replace("face_", "").lower()
                q_mem = q_mem.filter(
                    (RelevantMemoryModel.person == query.face_id) |
                    (RelevantMemoryModel.person.ilike(f"%{clean_id}%"))
                )
            elif isinstance(query, str) and query.strip():
                clean_q = query.strip()
                q_mem = q_mem.filter(
                    (RelevantMemoryModel.summary.ilike(f"%{clean_q}%")) |
                    (RelevantMemoryModel.title.ilike(f"%{clean_q}%"))
                )
            
            for m in q_mem.all():
                dom_m = self._to_domain(m)
                if tags:
                    m_tags = getattr(dom_m, "tags", []) or []
                    if any(t in m_tags for t in tags):
                        results.append(dom_m)
                else:
                    results.append(dom_m)

            # 2. Fetch Semantic Nodes (Knowledge Graph)
            q_sem = session.query(SemanticNodeModel)
            if query is not None and hasattr(query, "face_id") and query.face_id is not None:
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
            if query is not None and hasattr(query, "face_id") and query.face_id is not None:
                clean_id = query.face_id.replace("face_", "").lower()
                q_ep = q_ep.filter(
                    (EpisodeModel.person == query.face_id) |
                    (EpisodeModel.person.ilike(f"%{clean_id}%"))
                )
                
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

        # Multi-factor Memory Ranking:
        # Score = w_rec * Recency + w_conf * Confidence + w_imp * Importance + w_use * Usefulness
        now_ts = datetime.now().timestamp()

        def compute_metrics(m: RelevantMemory) -> tuple[float, float, float, float, float]:
            if m.timestamp:
                m_ts = m.timestamp.timestamp() if isinstance(m.timestamp, datetime) else now_ts
                age_hours = max(0.0, (now_ts - m_ts) / 3600.0)
                recency_score = 1.0 / (1.0 + age_hours / 24.0)
            else:
                recency_score = 0.5

            conf_score = getattr(m, "confidence", 0.9) or 0.9
            imp_val = m.importance.value if hasattr(m.importance, "value") else int(m.importance or 2)
            imp_score = min(1.0, imp_val / 3.0)
            use_score = getattr(m, "historical_usefulness", 0.5) or 0.5
            final_score = 0.35 * recency_score + 0.30 * conf_score + 0.20 * imp_score + 0.15 * use_score
            return final_score, recency_score, conf_score, imp_score, use_score

        results.sort(key=lambda m: compute_metrics(m)[0], reverse=True)

        if results:
            print(f"\n🧠 [Memory Ranking & Retrieval] Evaluated {len(results)} candidate memories:")
            for idx, m in enumerate(results[:5]):
                f_score, r_sc, c_sc, i_sc, u_sc = compute_metrics(m)
                lbl = m.title or (m.summary[:35] if m.summary else m.memory_id)
                print(f"   Candidate #{idx+1}: [{m.memory_id}] {lbl}")
                print(f"     • Recency={r_sc:.2f} | Confidence={c_sc:.2f} | Importance={i_sc:.2f} | Usefulness={u_sc:.2f} => Score={f_score:.3f}")
            winner = results[0]
            w_score = compute_metrics(winner)[0]
            w_lbl = winner.title or (winner.summary[:35] if winner.summary else winner.memory_id)
            print(f"   🏆 Selected Winner: [{winner.memory_id}] {w_lbl} (Final Weighted Score: {w_score:.3f})\n")

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
