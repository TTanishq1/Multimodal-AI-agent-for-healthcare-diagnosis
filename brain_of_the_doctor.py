# if you dont use pipenv uncomment the following:
from dotenv import load_dotenv
load_dotenv()

"""
Legacy multimodal image interface + new lightweight fusion wrapper.

The original Groq‑based image analysis is kept for backwards compatibility,
but the recommended entry point for the app is now
``get_multimodal_assessment`` which uses the fusion + confidence services.
"""

import base64
import os
from datetime import datetime
from typing import Any, Dict, Optional

try:
    # Optional – the app can run without Groq installed.
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Groq = None

from app.services.fusion_service import fuse
from app.services.confidence_service import compute_action
from app.services.history_service import get_history_summary, save_visit


GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


class GroqLLMClient:
    """
    Simple wrapper to make Groq compatible with fusion_service's llm_client interface.
    
    The fusion service expects an object with a generate(prompt: str) method that returns
    JSON string or dict.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/llama-4-maverick-17b-128e-instruct"):
        """
        Initialize Groq LLM client optimized for medical accuracy.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: Model to use (default: llama-4-maverick-17b-128e-instruct - Llama 4 Maverick)
                  Maverick has 128 experts vs Scout's 16, providing superior reasoning
                  capabilities for complex medical diagnosis tasks.
        """
        if Groq is None:
            raise ValueError("Groq library is not installed")
        
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be set")
        
        self.client = Groq(api_key=self.api_key)
        self.model = model
    
    def generate(self, prompt: str) -> str:
        """
        Generate response from prompt. Returns JSON string.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            JSON string response
        """
        try:
            # Try with JSON mode first (if supported by model)
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical expert. Always respond with valid JSON only, no markdown, no code blocks, just pure JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.model,
                    temperature=0.3,  # Lower temperature for more consistent, accurate responses
                    response_format={"type": "json_object"}  # Force JSON output
                )
            except Exception:
                # Fallback if JSON mode not supported
                chat_completion = self.client.chat.completions.create(
    messages=[
                        {
                            "role": "system",
                            "content": "You are a medical expert. CRITICAL: Respond ONLY with valid JSON. No markdown, no code blocks, no explanations before or after. Just pure JSON starting with { and ending with }."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model=self.model,
                    temperature=0.3,
                )
            
            response = chat_completion.choices[0].message.content
            
            # Clean up response - remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]  # Remove ```json
            if response.startswith("```"):
                response = response[3:]   # Remove ```
            if response.endswith("```"):
                response = response[:-3]  # Remove trailing ```
            response = response.strip()
            
            return response
        except Exception as e:
            raise Exception(f"Groq LLM generation failed: {str(e)}")


def encode_image(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# --- Legacy single‑shot image + text analysis ---------------------------------

QUERY_DEFAULT = "Is there something wrong with my face?"
MODEL_DEFAULT = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Maverick for superior medical accuracy


def analyze_image_with_query(query: str, model: str, encoded_image: str) -> str:
    """
    Backwards‑compatible Groq multimodal call.

    If Groq is not available this falls back to a short deterministic message so
    that imports and simple runs do not fail when offline.
    """
    if Groq is None:
        return "Image analysis model is not configured; using offline fallback description only."

    api_key = GROQ_API_KEY
    if not api_key or api_key == "your_groq_api_key_here" or api_key == "":
        raise ValueError("GROQ_API_KEY must be set in environment or .env file")
    
    client = Groq(api_key=api_key)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"},
                },
            ],
        }
    ]
    chat_completion = client.chat.completions.create(messages=messages, model=model)
    return chat_completion.choices[0].message.content


# --- New fused multimodal assessment -----------------------------------------

def get_multimodal_assessment(
    image_summary: str,
    image_conf: float,
    transcript: str,
    transcript_conf: float,
    patient_id: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    High‑level helper used by the Gradio app and local API.

    - Pulls a brief history summary from SQLite
    - Calls the fusion service (LLM optional)
    - Computes a simple triage / follow‑up action
    - Persists the visit for future history conditioning
    """
    history_summary = get_history_summary(patient_id)

    fusion_result = fuse(
        image_summary=image_summary,
        image_conf=image_conf,
        transcript=transcript,
        transcript_conf=transcript_conf,
        history_summary=history_summary,
        llm_client=llm_client,
    )

    action_result = compute_action(
        fusion_conf=fusion_result.get("fusion_confidence", 0.5),
        image_conf=image_conf,
        transcript_conf=transcript_conf,
        fused_findings=fusion_result.get("simple_findings"),
        conflict_flag=False,
    )

    # Persist visit including any raw LLM output for auditing.
    save_visit(
        patient_id=patient_id,
        transcript=transcript,
        image_summary=image_summary,
        fusion_result=fusion_result,
        timestamp=datetime.utcnow().isoformat(timespec="seconds"),
    )

    return {
        "fusion_result": fusion_result,
        "action_result": action_result,
        "history_summary": history_summary,
    }

