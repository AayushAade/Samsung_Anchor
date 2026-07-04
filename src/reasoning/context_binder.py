import json
import re
from google import genai
from google.genai import types

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
                self.client = genai.Client(api_key=self.api_key)
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
                
                # Request JSON format using the modern Client.models.generate_content API
                response = self.client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                
                if response and response.text:
                    try:
                        result = json.loads(response.text.strip())
                        return {
                            "extracted_name": result.get("extracted_name"),
                            "relationship": result.get("relationship")
                        }
                    except json.JSONDecodeError:
                        # Fallback for minor formatting edge cases
                        text = response.text.strip()
                        text = re.sub(r"```json|```", "", text).strip()
                        return json.loads(text)
            except Exception as e:
                print(f"[Context Binder Warning] Gemini API call failed: {e}. Falling back to local heuristics.")

        # Local rule-based fallback
        return self._local_heuristics_parse(transcript)

    def _local_heuristics_parse(self, transcript):
        """Rule-based parsing fallback for offline usage or missing API key."""
        transcript_lower = transcript.lower()
        
        # 0. Check for specific direct address relation pattern first (e.g., "Mark, your daughter is calling")
        direct_address_match = re.search(
            r"\b([a-z]+),\s+your\s+(son|daughter|grandson|granddaughter|wife|husband|friend|doctor|caregiver|nurse|niece|nephew)\b",
            transcript_lower
        )
        if direct_address_match:
            return {
                "extracted_name": direct_address_match.group(1).capitalize(),
                "relationship": direct_address_match.group(2).capitalize()
            }

        extracted_name = None
        relationship = None
        
        # Match relationship tags
        # E.g. "it's your son, Mark" -> relationship is Son
        rel_match = re.search(
            r"\b(son|daughter|grandson|granddaughter|wife|husband|friend|doctor|caregiver|nurse|niece|nephew)\b", 
            transcript_lower
        )
        if rel_match:
            relationship = rel_match.group(1).capitalize()
        else:
            # Map indirect terms to standard caregiver-friendly relationship types
            relationship_map = {
                "dad": "Child",
                "father": "Child",
                "mom": "Child",
                "mother": "Child",
                "grandpa": "Grandchild",
                "grandma": "Grandchild",
                "grandmother": "Grandchild",
                "grandfather": "Grandchild",
                "uncle": "Niece/Nephew",
                "aunt": "Niece/Nephew"
            }
            for term, rel in relationship_map.items():
                if term in transcript_lower:
                    relationship = rel
                    break
        
        # Smart Name Extraction (Identify ANY name through grammatical structure/direct address)
        # Normalize transcript: remove punctuation but keep capitalization
        clean_text = re.sub(r"[^\w\s']", " ", transcript)
        words = clean_text.split()
        
        if words:
            # Functional English stop words and common particles
            functional_words = {
                "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", 
                "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", 
                "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", 
                "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", 
                "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", 
                "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", 
                "about", "against", "between", "into", "through", "during", "before", "after", "above", 
                "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", 
                "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", 
                "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", 
                "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", 
                "should", "now", "hey", "hi", "hello", "greetings", "good", "morning", "afternoon", 
                "evening", "day", "yesterday", "today", "tomorrow", "monday", "tuesday", "wednesday", 
                "thursday", "friday", "saturday", "sunday", "january", "february", "march", "april", 
                "may", "june", "july", "august", "september", "october", "november", "december",
                "grandpa", "grandma", "grandfather", "grandmother", "dad", "mom", "father", "mother",
                "son", "daughter", "brother", "sister", "caregiver", "doctor", "friend", "nurse"
            }

            for w in words:
                # We check for any capitalized alphabetic word that is not a functional word
                if w.istitle() and w.lower() not in functional_words and w.isalpha():
                    extracted_name = w
                    break

            # Absolute Fallback using original regex patterns if no name was resolved grammatically
            if not extracted_name:
                relationship_match = re.search(
                    r"\b(?:it's|its|i am|i'm)\s+(?:your\s+)?(?:son|daughter|grandson|granddaughter|wife|husband|friend|doctor|caregiver|nurse|niece|nephew)\s+([a-z]+)", 
                    transcript_lower
                )
                if relationship_match:
                    extracted_name = relationship_match.group(1).capitalize()
                else:
                    match = re.search(r"\b(?:it's|its|i am|i'm|my name is)\s+([a-z]+)", transcript_lower)
                    if match:
                        name_candidate = match.group(1).capitalize()
                        if name_candidate.lower() not in ["your", "my", "the", "a", "an"]:
                            match_next = re.search(r"\b(?:it's|its|i am|i'm|my name is)\s+(?:your|my|the|a|an)\s+([a-z]+)", transcript_lower)
                            if match_next:
                                name_candidate = match_next.group(1).capitalize()
                        extracted_name = name_candidate
                    else:
                        match = re.search(r"\b(?:hi|hello|hey|greetings)\s+([a-z]+)", transcript_lower)
                        if match:
                            name_candidate = match.group(1).capitalize()
                            if name_candidate.lower() not in ["dad", "mom", "grandpa", "grandma", "grandson", "daughter", "son", "there", "friend"]:
                                extracted_name = name_candidate
                                
        return {
            "extracted_name": extracted_name,
            "relationship": relationship
        }

    def parse_location_query(self, query_text):
        """
        Parses a user voice/text query to determine what object they are looking for.
        Returns:
            dict: { "target_object": str or None }
        """
        if not query_text:
            return {"target_object": None}

        if self.use_api:
            try:
                prompt = f"""
                You are the query-parsing engine of Memora, an autonomous assistive AR wearable for Alzheimer's patients.
                Your task is to analyze the user's question and extract the target object they are asking to find.
                
                Guidelines:
                - Extract the object name in its singular, lowercase form (e.g., "phone" for "where is my phone?", "keys" for "where did I leave my keys?").
                - If the user is not asking to locate a specific object, return null.
                - Return a strict JSON response. Do not include markdown code block syntax.
                
                Query: "{query_text}"
                
                JSON Format:
                {{
                  "target_object": "extracted object name or null"
                }}
                """
                response = self.model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                
                if response and response.text:
                    try:
                        result = json.loads(response.text.strip())
                        return {
                            "target_object": result.get("target_object")
                        }
                    except json.JSONDecodeError:
                        text = response.text.strip()
                        text = re.sub(r"```json|```", "", text).strip()
                        return json.loads(text)
            except Exception as e:
                print(f"[Context Binder Warning] Gemini API query call failed: {e}. Falling back to local heuristics.")

        # Local rule-based fallback
        return self._local_location_query_parse(query_text)

    def _local_location_query_parse(self, query_text):
        """Rule-based parsing fallback for extracting queried object name."""
        query_lower = query_text.lower()
        
        # List of candidate items (similar to settings.TRACKED_OBJECTS)
        candidates = ["phone", "keys", "glasses", "backpack", "wallet", "remote", "book", "cup", "bottle", "handbag", "umbrella"]
        
        for candidate in candidates:
            # Match "phone", "cell phone", "keys", etc.
            if candidate in query_lower:
                return {"target_object": candidate}
            
            # Plural mappings
            if candidate.endswith("s") and candidate[:-1] in query_lower:
                return {"target_object": candidate}
            if candidate == "keys" and "key" in query_lower:
                return {"target_object": "keys"}
            if candidate == "glasses" and "glass" in query_lower:
                return {"target_object": "glasses"}

        # Try regex for "where is my [word]" or "where did I leave my [word]"
        match = re.search(r"\b(?:where is|where's|where did i (?:leave|put)|find my)\s+(?:my\s+)?([a-z]+)", query_lower)
        if match:
            obj = match.group(1)
            # Filter out common junk words
            if obj not in ["it", "that", "this", "my", "the", "a", "an", "some"]:
                return {"target_object": obj}

        return {"target_object": None}
