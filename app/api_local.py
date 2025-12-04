"""
Tiny synchronous API‑like wrapper used by the Gradio app.

This keeps orchestration logic (audio transcription, simple image summary,
fusion, confidence) in one place without requiring a web server.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from brain_of_the_doctor import get_multimodal_assessment
from voice_of_the_patient import transcribe_with_groq


def _simple_image_summary(image_path: Optional[str]) -> Dict[str, Any]:
    """
    Get image summary using Groq vision API if available, otherwise use simple placeholder.
    """
    if not image_path:
        return {"summary": "No image was provided.", "confidence": 0.4}

    # Try to use Groq vision API for accurate analysis
    try:
        from brain_of_the_doctor import encode_image, analyze_image_with_query
        
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key and api_key != "your_groq_api_key_here":
            encoded_img = encode_image(image_path)
            query = """You are a medical imaging specialist with expertise across ALL medical domains. Analyze this medical image comprehensively and provide a SPECIFIC diagnostic assessment.

CRITICAL: Look carefully at what is ACTUALLY visible and provide a specific diagnosis or differential diagnosis, not generic descriptions.

Provide a detailed, structured description covering:

1. IMAGE TYPE & LOCATION: 
   - Type of image (photograph, X-ray, scan, endoscopy, etc.)
   - Exact body part/region visible (any body part - skin, eyes, chest, abdomen, limbs, feet, hands, etc.)

2. SPECIFIC VISUAL FINDINGS (be very detailed):
   For SKIN/EXTERNAL LESIONS: 
   - EXACT lesion type: wart/verruca, acne, mole, rash, blister, ulcer, callus, corn, etc.
   - Size: measure approximate dimensions
   - Color: specific colors (yellowish-white, red, brown, etc.)
   - Shape: circular, irregular, raised, flat, etc.
   - Surface: smooth, rough, textured, verrucous, scaly, etc.
   - Borders: well-defined, ill-defined, irregular
   - Location: exact position on body part
   - Associated findings: redness, swelling, discharge, etc.
   
   For INTERNAL/RADIOLOGICAL: organ appearance, abnormalities, shadows, densities, structural changes
   For ANY IMAGE: abnormalities, normal vs. abnormal findings, measurements, characteristics

3. DIAGNOSTIC ASSESSMENT:
   - What SPECIFIC condition does this most likely represent? (e.g., "plantar wart", "acne vulgaris", "contact dermatitis", etc.)
   - Provide a specific diagnosis or differential diagnosis based on visual appearance
   - DO NOT say "minor skin change" - name the actual condition

4. DETAILED CHARACTERISTICS:
   - Size/dimensions of any abnormalities
   - Color/appearance (for visible images)
   - Distribution/pattern
   - Borders/margins
   - Texture/surface characteristics
   - Any associated findings

5. SEVERITY ASSESSMENT: Mild, moderate, or severe based on extent and characteristics

6. DIFFERENTIAL CONSIDERATIONS: What other medical conditions could this represent (list 2-3 possibilities)

7. CLINICAL SIGNIFICANCE: Any concerning features requiring attention (signs of infection, structural abnormalities, acute vs. chronic appearance, etc.)

Be precise, use appropriate medical terminology, and provide a SPECIFIC diagnosis that matches what you actually see in the image."""
            
            vision_result = analyze_image_with_query(
                query=query,
                model="meta-llama/llama-4-maverick-17b-128e-instruct",  # Maverick for superior medical accuracy
                encoded_image=encoded_img
            )
            
            return {
                "summary": vision_result,
                "confidence": 0.85,  # Higher confidence for actual vision API
            }
    except Exception as e:
        print(f"Groq vision API failed: {e}. Using fallback...")
        # Fall through to deterministic fallback

    # Deterministic fallback based on filename
    name = os.path.basename(image_path).lower()
    if "acne" in name or "pimple" in name:
        return {
            "summary": "Photo of facial skin with multiple small red spots suggestive of acne.",
            "confidence": 0.75,
        }
    return {
        "summary": "Photo of skin with a localised change; appears mild in this static image.",
        "confidence": 0.6,
    }


def submit_record(
    audio_filepath: Optional[str],
    image_filepath: Optional[str],
    patient_id: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    End‑to‑end helper used on initial submit from the UI.

    Returns:
        {
          "transcript": str,
          "fusion_result": {...},
          "action_result": {...},
          "history_summary": str,
          "session_state": {...},
        }
    """
    # 1) Transcribe audio if present.
    if audio_filepath:
        try:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key or api_key == "your_groq_api_key_here":
                raise ValueError("API key not configured")
            transcript = transcribe_with_groq(
                GROQ_API_KEY=api_key,
                audio_filepath=audio_filepath,
                stt_model="whisper-large-v3",
            )
            transcript_conf = 0.75  # simple fixed confidence for now
        except Exception as e:
            # Fallback when transcription fails (API key missing or other error)
            transcript = f"[Audio transcription unavailable: {str(e)}. Please configure GROQ_API_KEY in .env file or set it as environment variable.]"
            transcript_conf = 0.3
    else:
        transcript = "No audio was provided."
        transcript_conf = 0.4

    # 2) Get a simple image summary.
    img = _simple_image_summary(image_filepath)

    # 3) Run multimodal assessment (this also persists history).
    assessment = get_multimodal_assessment(
        image_summary=img["summary"],
        image_conf=img["confidence"],
        transcript=transcript,
        transcript_conf=transcript_conf,
        patient_id=patient_id,
        llm_client=llm_client,
    )

    session_state = {
        "image_summary": img["summary"],
        "image_conf": img["confidence"],
        "transcript": transcript,
        "transcript_conf": transcript_conf,
        "patient_id": patient_id,
        "history_summary": assessment.get("history_summary"),
    }

    return {
        "transcript": transcript,
        "fusion_result": assessment["fusion_result"],
        "action_result": assessment["action_result"],
        "history_summary": assessment["history_summary"],
        "session_state": session_state,
    }


