import os
from src.llm.reasoning_client import ReasoningClient

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class GeminiReasoningClient(ReasoningClient):
    """
    Production client for Google's Gemini Models.
    Implements the abstract ReasoningClient interface.
    """
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        if not HAS_GENAI:
            raise ImportError("Please install the google-genai package.")
            
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("[Warning] GEMINI_API_KEY not found in environment.")
            
        # Using the new google-genai SDK 
        self.client = genai.Client()
        self.model_name = model_name

    def generate_cue(self, structured_prompt: str) -> str:
        """
        Takes the strictly formatted ContextBuilder prompt and generates the natural language cue.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=structured_prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"[GeminiClient] Error generating cue: {e}")
            raise e
