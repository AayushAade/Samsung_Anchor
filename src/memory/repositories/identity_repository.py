import json
from datetime import datetime
from sqlalchemy.orm import Session
from src.memory.models import Identity, IdentityEvidence

class IdentityRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_all(self):
        with self.session_factory() as session:
            identities = session.query(Identity).all()
            return [self._to_dict(i) for i in identities]

    def get_by_id(self, identity_id: str):
        with self.session_factory() as session:
            identity = session.query(Identity).filter(Identity.identity_id == identity_id).first()
            if not identity:
                return None
            return self._to_dict(identity)

    def _to_dict(self, identity: Identity):
        ev_history = []
        if identity.evidence_history:
            if isinstance(identity.evidence_history, list):
                ev_history = identity.evidence_history
            elif isinstance(identity.evidence_history, str):
                try:
                    ev_history = json.loads(identity.evidence_history)
                except Exception:
                    pass

        return {
            "identity_id": identity.identity_id,
            "display_name": identity.display_name,
            "relationship": identity.relationship,
            "status": identity.status,
            "candidate_name": identity.candidate_name,
            "candidate_relationship": identity.candidate_relationship,
            "confidence": identity.confidence,
            "times_seen": identity.times_seen,
            "first_seen": identity.first_seen,
            "last_seen": identity.last_seen,
            "evidence_history": ev_history,
            "name": identity.display_name,
            "created_at": identity.first_seen,
            "updated_at": identity.last_seen
        }

    def register_anonymous(self, identity_id: str):
        with self.session_factory() as session:
            now_str = datetime.now().isoformat()
            new_identity = Identity(
                identity_id=identity_id,
                display_name=None,
                relationship=None,
                status="unconfirmed",
                confidence=0.0,
                times_seen=1,
                first_seen=now_str,
                last_seen=now_str,
                evidence_history=[]
            )
            session.add(new_identity)
            session.commit()
            return identity_id

    def increment_times_seen(self, identity_id: str):
        with self.session_factory() as session:
            identity = session.query(Identity).filter(Identity.identity_id == identity_id).first()
            if identity:
                identity.times_seen += 1
                identity.last_seen = datetime.now().isoformat()
                session.commit()
                return True
        return False

    def add_evidence(self, identity_id: str, name: str, relationship: str = None, raw_transcript: str = None):
        if not identity_id or not name:
            return None

        name = name.strip().capitalize()
        if relationship:
            relationship = relationship.strip().capitalize()

        with self.session_factory() as session:
            identity = session.query(Identity).filter(Identity.identity_id == identity_id).first()
            if not identity:
                return None
            
            if identity.status == "confirmed":
                return {
                    "name": identity.display_name,
                    "relationship": identity.relationship,
                    "confidence": 1.0,
                    "is_confirmed": True
                }

            evidence = session.query(IdentityEvidence).filter(
                IdentityEvidence.identity_id == identity_id,
                IdentityEvidence.heard_name == name
            ).first()

            now_str = datetime.now().isoformat()
            final_rel = relationship

            if evidence:
                evidence.count += 1
                evidence.updated_at = now_str
                final_rel = relationship or evidence.heard_relationship
                evidence.heard_relationship = final_rel
                new_count = evidence.count
            else:
                new_count = 1
                evidence = IdentityEvidence(
                    identity_id=identity_id,
                    heard_name=name,
                    heard_relationship=final_rel,
                    count=1,
                    created_at=now_str,
                    updated_at=now_str,
                    confidence=0.0
                )
                session.add(evidence)
                
            # Confidence logic
            if final_rel:
                confidence = 0.90 if new_count == 1 else 0.85
            else:
                confidence = 0.40
                if raw_transcript and raw_transcript.strip().lower() == name.lower():
                    confidence = 0.60
                if new_count == 2:
                    confidence = max(confidence, 0.70)
                elif new_count >= 3:
                    confidence = max(confidence, 0.80)

            evidence.confidence = confidence

            # Update identity
            ev_history = list(identity.evidence_history) if identity.evidence_history else []
            ev_history.append({
                "timestamp": now_str,
                "heard_name": name,
                "heard_relationship": final_rel,
                "raw_transcript": raw_transcript,
                "confidence": confidence,
                "count": new_count
            })
            
            is_confirmed = (confidence >= 0.80)
            status = "confirmed" if is_confirmed else "unconfirmed"

            if is_confirmed:
                identity.display_name = name
                identity.relationship = final_rel
            
            identity.status = status
            identity.candidate_name = name
            identity.candidate_relationship = final_rel
            identity.confidence = confidence
            identity.last_seen = now_str
            # Need to assign new list to trigger SQLAlchemy JSON update
            identity.evidence_history = ev_history 

            session.commit()

            return {
                "name": name,
                "relationship": final_rel,
                "confidence": confidence,
                "is_confirmed": is_confirmed
            }
