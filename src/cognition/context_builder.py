from __future__ import annotations

from typing import List
from src.cognition.memory_models import RelevantMemory
from src.interaction.events import PresenceEvent

class ContextBuilder:
    """
    Constructs a highly structured, rigid prompt for the Reasoning Client.
    """
    
    def build_prompt(
        self, 
        event: PresenceEvent, 
        memories: List[RelevantMemory], 
        current_location: str, 
        current_time: str
    ) -> str:
        """
        Builds the context string matching the rigorous spec.
        """
        
        # 1. Current Situation
        situation = f"- {event.name or 'Unknown person'} detected in {current_location}\n- Time: {current_time}"
        
        # 2. Relevant Memories
        memory_lines = []
        if not memories:
            memory_lines.append("- No past memories retrieved.")
        else:
            for mem in memories:
                line = f"- {mem.summary}"
                if mem.commitments:
                    line += f" (Commitments: {', '.join(mem.commitments)})"
                memory_lines.append(line)
                
        memories_str = "\n".join(memory_lines)
        
        # 3. User Profile
        relationship = event.relationship or "Unknown"
        profile = f"- {event.name} is {relationship}."
        
        # 4. Current Environment
        environment = f"- {current_location}"
        
        # Final Prompt Assembly
        prompt = f"""Current Situation:
{situation}

Relevant Memories:
{memories_str}

User Profile:
{profile}

Current Environment:
{environment}

Task:
Generate one short, natural memory cue to help the user remember the context of this person.
Do not hallucinate. Do not act like an AI. Just provide a natural reminder.
"""
        return prompt.strip()
