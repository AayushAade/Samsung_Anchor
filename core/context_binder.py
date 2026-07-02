import json
import re
import google.generativeai as genai

# Import settings
from config import settings

class MemoraContextBinder:
    def __init__(self, api_key=None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.use_api = True
        
        if not self.api_key:
            print("[Context Binder Warning] GEMINI_API_KEY is not set. Context Binder will run in local rule-based fallback mode.")
            self.use_api = False
        else:
            try:
                genai.configure(api_key=self.api_key)
                # Use gemini-1.5-flash as the standard fast LLM model
                self.model = genai.GenerativeModel("gemini-1.5-flash")
            except Exception as e:
                print(f"[Context Binder Warning] Failed to configure Gemini API client: {e}. Enabling local fallback.")
                self.use_api = False

    def parse_transcript(self, transcript):
        """
        Parses ambient speech transcript to extract name and relationship.
        Returns:
            dict: { "extracted_name": str or None, "relationship": str or None }
        """
        if not transcript:
            return {"extracted_name": None, "relationship": None}

        if self.use_api:
            try:
                prompt = f"""
                You are the context-binding engine of Memora, an autonomous assistive AR wearable for Alzheimer's patients.
                Your task is to analyze the following transcription of ambient speech and extract the name and relationship (if any) of the person speaking to the patient.
                
                Guidelines:
                - Extract the name of the person who is approaching, greeting, or introducing themselves.
                - Extract the relationship (e.g. Daughter, Spouse, Son, Friend, Caregiver, Doctor, Grandson) if explicitly stated or strongly implied (e.g., "Hi Dad, it's Sarah" implies relationship "Daughter" and name "Sarah").
                - If no name is mentioned, return null for name.
                - Return a strict JSON response. Do not include markdown code block syntax.
                
                Transcript: "{transcript}"
                
                JSON Format:
                {{
                  "extracted_name": "extracted name or null",
                  "relationship": "extracted relationship or null"
                }}
                """
                
                # Request JSON format from the Gemini model
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                if response and response.text:
                    try:
                        result = json.loads(response.text.strip())
                        # Standardize keys
                        return {
                            "extracted_name": result.get("extracted_name"),
                            "relationship": result.get("relationship")
                        }
                    except json.JSONDecodeError:
                        # Fallback parsing in case model doesn't return clean json despite config
                        text = response.text.strip()
                        # Strip markdown if any
                        text = re.sub(r"```json|```", "", text).strip()
                        return json.loads(text)
                        
            except Exception as e:
                print(f"[Context Binder Warning] Gemini API call failed: {e}. Falling back to local heuristics.")
                # fall through to local heuristics

        # Local heuristics fallback parser
        return self._local_heuristics_parse(transcript)

    def _local_heuristics_parse(self, transcript):
        """Rule-based parsing fallback for offline usage or missing API key."""
        transcript_lower = transcript.lower()
        
        # Simple patterns
        # 1. "Hi Dad, it's Sarah" -> Daughter, Sarah
        # 2. "Hey Grandpa, it's your grandson Mark"
        # 3. "My name is Sarah"
        # 4. "I'm Mark"
        
        extracted_name = None
        relationship = None
        
        # Check for explicit relationship terms first
        if "granddaughter" in transcript_lower:
            relationship = "Granddaughter"
        elif "daughter" in transcript_lower:
            relationship = "Daughter"
        elif "grandson" in transcript_lower:
            relationship = "Grandson"
        elif "son" in transcript_lower:
            relationship = "Son"
        elif "wife" in transcript_lower or "husband" in transcript_lower:
            relationship = "Spouse"
        elif "doctor" in transcript_lower:
            relationship = "Doctor"
        elif "caregiver" in transcript_lower:
            relationship = "Caregiver"
        elif "friend" in transcript_lower:
            relationship = "Friend"
        else:
            # Fallback: Infer relationship from terms of address used to greet the patient
            relationship_map = {
                "dad": "Child",
                "father": "Child",
                "mom": "Child",
                "mother": "Child",
                "grandpa": "Grandchild",
                "grandfather": "Grandchild",
                "grandma": "Grandchild",
                "grandmother": "Grandchild",
                "uncle": "Niece/Nephew",
                "aunt": "Niece/Nephew"
            }
            for term, rel in relationship_map.items():
                if term in transcript_lower:
                    relationship = rel
                    break
        
        # Heuristics for name extraction
        # 1. Check for "it's [your] [relationship] [name]" pattern first
        relationship_match = re.search(
            r"\b(?:it's|its|i am|i'm)\s+(?:your\s+)?(?:son|daughter|grandson|granddaughter|wife|husband|friend|doctor|caregiver|nurse|niece|nephew)\s+([a-z]+)", 
            transcript_lower
        )
        if relationship_match:
            extracted_name = relationship_match.group(1).capitalize()
        else:
            # 2. Try general patterns: "it's <name>", "my name is <name>", "i am <name>"
            match = re.search(r"\b(?:it's|its|i am|i'm|my name is)\s+([a-z]+)", transcript_lower)
            if match:
                name_candidate = match.group(1).capitalize()
                # Skip filler articles and pronouns
                if name_candidate.lower() in ["your", "my", "the", "a", "an"]:
                    match_next = re.search(r"\b(?:it's|its|i am|i'm|my name is)\s+(?:your|my|the|a|an)\s+([a-z]+)", transcript_lower)
                    if match_next:
                        name_candidate = match_next.group(1).capitalize()
                extracted_name = name_candidate
            # 3. Try "hi <name>" or "hello <name>"
            else:
                match = re.search(r"\b(?:hi|hello|hey|greetings)\s+([a-z]+)", transcript_lower)
                if match:
                    name_candidate = match.group(1).capitalize()
                    # Ensure it's not a common relationship term or greetings word
                    if name_candidate.lower() not in ["dad", "mom", "grandpa", "grandma", "grandson", "daughter", "son", "there", "friend"]:
                        extracted_name = name_candidate
                    
        return {
            "extracted_name": extracted_name,
            "relationship": relationship
        }
