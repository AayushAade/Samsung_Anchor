from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class SystemState(Base):
    __tablename__ = 'system_state'
    
    key = Column(String, primary_key=True)
    value = Column(String)

class Identity(Base):
    __tablename__ = 'identities'
    
    identity_id = Column(String, primary_key=True)
    display_name = Column(String, nullable=True)
    relationship = Column(String, nullable=True)
    status = Column(String, default="unconfirmed")
    candidate_name = Column(String, nullable=True)
    candidate_relationship = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    times_seen = Column(Integer, default=1)
    first_seen = Column(String)
    last_seen = Column(String)
    evidence_history = Column(JSON, default=list)

class IdentityEvidence(Base):
    __tablename__ = 'identity_evidence'
    
    identity_id = Column(String, ForeignKey('identities.identity_id'), primary_key=True)
    heard_name = Column(String, primary_key=True)
    heard_relationship = Column(String, nullable=True)
    count = Column(Integer, default=1)
    confidence = Column(Float, default=0.0)
    created_at = Column(String)
    updated_at = Column(String)

class Object(Base):
    __tablename__ = 'objects'
    
    name = Column(String, primary_key=True)
    last_seen = Column(String)
    x = Column(Float)
    y = Column(Float)
    room = Column(String)
    bounding_box = Column(JSON, nullable=True)

class ObjectHistory(Base):
    __tablename__ = 'object_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    object_name = Column(String, ForeignKey('objects.name'))
    timestamp = Column(String)
    x = Column(Float)
    y = Column(Float)
    room = Column(String)
    bounding_box = Column(JSON, nullable=True)

class EpisodeModel(Base):
    __tablename__ = 'episodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    location = Column(String, nullable=True)
    commitments = Column(JSON, default=list)
    tags = Column(JSON, default=list)

class RelevantMemoryModel(Base):
    __tablename__ = 'relevant_memories'
    
    memory_id = Column(String, primary_key=True)
    memory_type = Column(String, nullable=False)
    importance = Column(Integer, default=2) # 2 = NORMAL
    title = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    person = Column(String, nullable=True)
    location = Column(String, nullable=True)
    timestamp = Column(String, nullable=True)
    commitments = Column(JSON, default=list)
    tags = Column(JSON, default=list)

class SemanticNodeModel(Base):
    """
    Represents a consolidated knowledge graph node.
    """
    __tablename__ = 'semantic_nodes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject = Column(String, nullable=False) # e.g. "Sarah"
    predicate = Column(String, nullable=False) # e.g. "favorite_color"
    object_val = Column(String, nullable=False) # e.g. "blue"
    category = Column(String, nullable=False) # MemoryCategory
    importance = Column(Integer, default=2) 
    confidence = Column(Float, default=1.0) # 0.0 to 1.0, decays over time
    last_reinforced = Column(String, nullable=False) # ISO Timestamp
    
    # Meta-Cognitive Metadata
    evidence_count = Column(Integer, default=1)
    confirmation_count = Column(Integer, default=0)
    correction_count = Column(Integer, default=0)
    contradiction_count = Column(Integer, default=0)
    last_confirmed = Column(String, nullable=True) # ISO Timestamp
    last_corrected = Column(String, nullable=True) # ISO Timestamp
    verification_status = Column(String, default="Unverified")
    historical_usefulness = Column(Float, default=0.5) # 0.0 (annoying) to 1.0 (helpful)

class InteractionRecordModel(Base):
    __tablename__ = 'interaction_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False) # ISO Timestamp
    face_id = Column(String, nullable=False)
    decision = Column(String, nullable=False) # 'INTERRUPT' or 'SILENCE'
    selected_memory_ids = Column(JSON, default=list) # IDs of SemanticNodes or Episodes
    prompt_sent = Column(String, nullable=True)
    generated_response = Column(String, nullable=True)

class FeedbackEventModel(Base):
    __tablename__ = 'feedback_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    interaction_id = Column(Integer, ForeignKey('interaction_records.id'), nullable=True)
    source = Column(String, nullable=False) # e.g., 'VOICE', 'MANUAL'
    feedback_type = Column(String, nullable=False) # e.g., 'CORRECTION', 'CONFIRMATION'
    content = Column(String, nullable=True) # The actual correction text
    processed = Column(Integer, default=0) # 0 = No, 1 = Yes
