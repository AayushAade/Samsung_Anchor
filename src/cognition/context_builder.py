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
        social: Optional[Any] = None,
        assistance: Optional[Any] = None,
        conversation: Optional[Any] = None,
        clinical: Optional[Any] = None,
        perception: Optional[Any] = None
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

        # 7. Assistance Constraint
        assistance_constraint = ""
        if assistance:
            lvl_code = getattr(assistance, "level_code", 3)
            lvl_label = getattr(assistance, "level_label", "Level 3: Context Restoration")
            assistance_constraint = f"\n- TARGET ASSISTANCE LEVEL: {lvl_label}"
            if lvl_code == 1:
                assistance_constraint += "\n- Provide ONLY light positive encouragement. Do NOT give instructions or direct cues."
            elif lvl_code == 2:
                assistance_constraint += "\n- Provide ONLY a subtle, indirect hint. Do NOT give away the full situation or answer."
            elif lvl_code == 3:
                assistance_constraint += "\n- Provide a supportive context restoration cue."
            elif lvl_code == 4:
                assistance_constraint += "\n- Provide clear step-by-step guidance."
            elif lvl_code == 5:
                assistance_constraint += "\n- Provide a direct, gentle safety instruction."

        # 8. Conversation Strategy Constraint
        conversation_section = ""
        if conversation:
            state_val = getattr(getattr(conversation, "state", None), "value", "Responding")
            speaker_val = getattr(getattr(conversation, "active_speaker", None), "value", "Patient")
            strat_val = getattr(getattr(conversation, "response_strategy", None), "value", "Context Restoration")
            conversation_section = f"\nConversation Context:\n- State: {state_val}\n- Active Speaker: {speaker_val}\n- Selected Response Strategy: {strat_val}\n"
            assistance_constraint += f"\n- MANDATORY RESPONSE STRATEGY: {strat_val}. Strictly generate text matching this strategy."

        # 9. Clinical & Medication Context
        clinical_section = ""
        if clinical:
            pref = getattr(clinical, "communication_preferences", "")
            meds = getattr(clinical, "pending_medications", [])
            emergency = getattr(clinical, "emergency_state", None)
            if pref:
                clinical_section += f"\nClinical Preferences:\n- Communication Preference: {pref}\n"
            if meds:
                clinical_section += f"- Pending Medication: {', '.join(meds)}\n"
            if emergency and getattr(emergency, "active", False):
                clinical_section += f"- EMERGENCY OVERRIDE: {getattr(emergency, 'trigger_reason', 'Active Emergency')}\n"
                assistance_constraint += f"\n- CLINICAL SAFETY OVERRIDE: Deliver immediate safety guidance calmly and directly."

        # 10. Edge Perception Context
        perception_section = ""
        if perception:
            room = getattr(getattr(perception, "current_room", None), "value", "Living Room")
            activity = getattr(getattr(perception, "detected_activity", None), "value", "Sitting")
            objs = [o.object_name if hasattr(o, "object_name") else str(o) for o in getattr(perception, "detected_objects", [])]
            auds = [a.event_type.value if hasattr(a, "event_type") and hasattr(a.event_type, "value") else str(a) for a in getattr(perception, "audio_events", [])]
            perception_section = f"\nEdge Perception Context:\n- Active Room: {room}\n- Detected Activity: {activity}\n"
            if objs:
                perception_section += f"- Tracked Household Objects: {', '.join(objs)}\n"
            if auds:
                perception_section += f"- Audio Events: {', '.join(auds)}\n"

        # Final Prompt Assembly
        prompt = f"""Current Situation:
{situation}

Relevant Memories:
{memories_str}

User Profile:
{profile}

Current Environment:
{environment}
{orientation_section}{relationship_section}{conversation_section}{clinical_section}{perception_section}
Task:
Generate one short, natural memory cue to help the user remember the context of this person and preserve their warm relationship.
CRITICAL HUMAN-CENTERED GUIDELINES (DIGNITY FILTER):
- Speak calmly, gently, and warmly.
- Never overload the user: present ONE simple idea at a time.
- Never say "You forgot". Instead, use phrases like "Here is a gentle reminder" or "By the way".
- Never quiz or test the user. Never ask "Do you remember who this is?".
- Encourage warm human interaction, do not dominate the conversation.
- Avoid all medical jargon.
- Validate their reality; never argue or correct harshly.{assistance_constraint}
- Do not hallucinate. Do not act like an AI. Just provide a natural, compassionate reminder.
"""
        return prompt.strip()
