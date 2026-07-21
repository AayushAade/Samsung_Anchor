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
        current_time: str,
        orientation: Optional[Any] = None,
        social: Optional[Any] = None
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
        
        # 5. Orientation Anchor
        orientation_section = ""
        if orientation:
            stage = getattr(orientation, "routine_stage", "Daytime Routine")
            recent = getattr(orientation, "recent_activity", None)
            upcoming = getattr(orientation, "upcoming_activity", None)
            orientation_section = f"\nDaily Orientation Anchor:\n- Routine Stage: {stage}"
            if recent:
                orientation_section += f"\n- Recent Activity: {recent}"
            if upcoming:
                orientation_section += f"\n- Next Activity: {upcoming}"
            orientation_section += "\n"

        # 6. Relationship Context
        relationship_section = ""
        if social and getattr(social, "active_profile", None):
            prof = social.active_profile
            greeting = getattr(prof, "preferred_greeting", "")
            freq = getattr(prof, "visit_frequency", "")
            dates = getattr(prof, "important_dates", [])
            relationship_section = f"\nRelationship Context:\n- Preferred Greeting: {greeting}\n- Visit Cadence: {freq}"
            if dates:
                relationship_section += f"\n- Milestones: {', '.join(dates)}"
            relationship_section += "\n"

        # Final Prompt Assembly
        prompt = f"""Current Situation:
{situation}

Relevant Memories:
{memories_str}

User Profile:
{profile}

Current Environment:
{environment}
{orientation_section}{relationship_section}
Task:
Generate one short, natural memory cue to help the user remember the context of this person and preserve their warm relationship.
CRITICAL HUMAN-CENTERED GUIDELINES (DIGNITY FILTER):
- Speak calmly, gently, and warmly.
- Never overload the user: present ONE simple idea at a time.
- Never say "You forgot". Instead, use phrases like "Here is a gentle reminder" or "By the way".
- Never quiz or test the user. Never ask "Do you remember who this is?".
- Encourage warm human interaction, do not dominate the conversation.
- Avoid all medical jargon.
- Validate their reality; never argue or correct harshly.
- Do not hallucinate. Do not act like an AI. Just provide a natural, compassionate reminder.
"""
        return prompt.strip()
