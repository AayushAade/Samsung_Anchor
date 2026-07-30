import json
from datetime import datetime
from src.memory.models import SemanticNodeModel
from src.cognition.memory_taxonomy import MemoryCategory, MemoryImportance
from src.cognition.episode import Episode
from src.llm.reasoning_client import ReasoningClient

class MemoryConsolidator:
    """
    Extracts semantic facts from an Episode and merges them into the Knowledge Graph.
    This mimics Hippocampal consolidation.
    """
    def __init__(self, session_factory, llm_client: ReasoningClient):
        self.session_factory = session_factory
        self.llm = llm_client

    def consolidate(self, episode: Episode):
        """
        Extracts structured JSON facts from the episode and updates the graph.
        """
        # 1. Ask the LLM to extract strict JSON facts.
        prompt = self._build_extraction_prompt(episode)
        try:
            # We assume the LLM client can return valid JSON arrays based on our strict prompt
            response_text = self.llm.generate_cue(prompt)
            # Find the JSON array inside the response
            json_str = response_text[response_text.find("["):response_text.rfind("]")+1]
            extracted_facts = json.loads(json_str)
        except Exception as e:
            print(f"[MemoryConsolidator] Failed to extract facts: {e}")
            return

        # 2. Merge into the Knowledge Graph
        with self.session_factory() as session:
            for fact in extracted_facts:
                subject = fact.get("subject", "").strip().lower()
                predicate = fact.get("predicate", "").strip().lower()
                object_val = fact.get("object", "").strip().lower()
                
                if not subject or not predicate or not object_val:
                    continue

                category_str = fact.get("category", "fact").upper()
                try:
                    category = MemoryCategory[category_str].value
                except KeyError:
                    category = MemoryCategory.FACT.value
                    
                importance = int(fact.get("importance", 2))
                
                # Check if this exact edge already exists
                existing_node = session.query(SemanticNodeModel).filter_by(
                    subject=subject,
                    predicate=predicate,
                    object_val=object_val
                ).first()
                
                now_str = datetime.now().isoformat()
                
                if existing_node:
                    # Reinforce the memory! 
                    existing_node.confidence = min(1.0, existing_node.confidence + 0.2)
                    existing_node.last_reinforced = now_str
                    # If this memory is repeated, its importance might bump up
                    existing_node.importance = max(existing_node.importance, importance)
                else:
                    # Create new memory
                    new_node = SemanticNodeModel(
                        subject=subject,
                        predicate=predicate,
                        object_val=object_val,
                        category=category,
                        importance=importance,
                        confidence=0.8, # Initial confidence is slightly below 1.0 until reinforced
                        last_reinforced=now_str
                    )
                    session.add(new_node)
            
            session.commit()
            print(f"[MemoryConsolidator] Consolidated {len(extracted_facts)} facts into Semantic Memory.")

    def _build_extraction_prompt(self, episode: Episode) -> str:
        return f"""
Analyze the following episode summary and extract concrete, long-term semantic facts.
Episode Summary: "{episode.summary}"
Commitments: {episode.commitments}

Return ONLY a JSON array of objects with the following keys:
- subject: (string, who or what the fact is about, e.g., "Sarah")
- predicate: (string, the relationship or action, e.g., "favorite_color", "visits_on", "has_condition")
- object: (string, the target or value, e.g., "blue", "tuesday", "asthma")
- category: (string, must be one of: RELATIONSHIP, PREFERENCE, ROUTINE, MEDICAL, COMMITMENT, SPATIAL, FACT)
- importance: (integer 1-4, where 4 is critical medical/safety, and 1 is trivial)

Example:
[
  {{"subject": "Sarah", "predicate": "favorite_color", "object": "blue", "category": "PREFERENCE", "importance": 1}},
  {{"subject": "Sarah", "predicate": "needs_medication", "object": "heart_pills", "category": "MEDICAL", "importance": 4}}
]
"""
