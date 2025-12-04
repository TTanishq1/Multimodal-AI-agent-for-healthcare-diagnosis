# API Local Documentation (app/api_local.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`api_local.py` yeh main orchestration file hai jo sabhi services ko coordinate karti hai. Yeh file audio transcription, image analysis, aur multimodal assessment ko combine karke final result deti hai.

### Main Responsibilities (मुख्य जिम्मेदारियां)

1. **Image Analysis** - Medical images ko analyze karna
2. **Audio Transcription** - Audio ko text mein convert karna
3. **Parallel Processing** - Dono tasks simultaneously run karna (speed ke liye)
4. **Multimodal Assessment** - Sab kuch combine karke final assessment dena

---

## Line-by-Line Code Explanation

### Lines 1-15: Imports
```python
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional

from brain_of_the_doctor import get_multimodal_assessment
from voice_of_the_patient import transcribe_with_groq
```
**Explanation:**
- `__future__ import annotations` - Type hints ke liye
- `os` - Environment variables access karne ke liye
- `ThreadPoolExecutor` - Parallel processing ke liye
- `as_completed` - Thread completion tracking ke liye
- `get_multimodal_assessment` - Main assessment function
- `transcribe_with_groq` - Audio transcription function

### Lines 18-101: Image Summary Function
```python
def _simple_image_summary(image_path: Optional[str]) -> Dict[str, Any]:
    """
    Get image summary using Groq vision API if available, otherwise use simple placeholder.
    """
```
**Explanation:**
Yeh function image ko analyze karke summary deti hai.

**Lines 22-23: No Image Check**
```python
if not image_path:
    return {"summary": "No image was provided.", "confidence": 0.4}
```
- Agar image na ho, toh default message return karta hai

**Lines 26-89: Vision API Try Block**
```python
try:
    from brain_of_the_doctor import encode_image, analyze_image_with_query
    
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key and api_key != "your_groq_api_key_here":
        encoded_img = encode_image(image_path)
        query = """You are a medical imaging specialist..."""
        
        vision_result = analyze_image_with_query(
            query=query,
            model="llama-3.2-90b-vision-preview",
            encoded_image=encoded_img
        )
        
        return {
            "summary": vision_result,
            "confidence": 0.85,
        }
except Exception as e:
    print(f"Groq vision API failed: {e}. Using fallback...")
```
**Explanation:**
- API key check karta hai
- Image ko base64 mein encode karta hai
- Detailed prompt banata hai jo medical specialist ko instruct karta hai
- Vision API call karta hai
- High confidence (0.85) return karta hai
- Agar fail ho, toh fallback use hota hai

**Lines 91-101: Fallback Logic**
```python
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
```
**Explanation:**
- Filename se condition guess karta hai
- Acne ke liye specific message
- Generic message agar kuch match na ho

### Lines 104-189: Submit Record Function
```python
def submit_record(
    audio_filepath: Optional[str],
    image_filepath: Optional[str],
    patient_id: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
```
**Explanation:**
Yeh main function hai jo sab kuch coordinate karti hai.

**Lines 122-138: Audio Transcription Function (Nested)**
```python
def transcribe_audio():
    """Transcribe audio in parallel thread."""
    if not audio_filepath:
        return "No audio was provided.", 0.4
    try:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "your_groq_api_key_here":
            raise ValueError("API key not configured")
        transcript = transcribe_with_groq(
            GROQ_API_KEY=api_key,
            audio_filepath=audio_filepath,
            stt_model="whisper-large-v3-turbo",
        )
        return transcript, 0.75
    except Exception as e:
        return f"[Audio transcription unavailable: {str(e)}...]", 0.3
```
**Explanation:**
- Nested function jo parallel thread mein run hogi
- Audio transcription handle karti hai
- Error handling ke saath
- Confidence score return karti hai

**Lines 140-142: Image Analysis Function (Nested)**
```python
def analyze_image():
    """Analyze image in parallel thread."""
    return _simple_image_summary(image_filepath)
```
**Explanation:**
- Simple wrapper jo image analysis karti hai
- Parallel thread mein run hogi

**Lines 145-162: Parallel Processing**
```python
# Run audio transcription and image analysis in parallel
transcript = "No audio was provided."
transcript_conf = 0.4
img = {"summary": "No image was provided.", "confidence": 0.4}

with ThreadPoolExecutor(max_workers=2) as executor:
    futures = {}
    if audio_filepath:
        futures['audio'] = executor.submit(transcribe_audio)
    if image_filepath:
        futures['image'] = executor.submit(analyze_image)
    
    # Wait for results and assign them correctly
    for key, future in futures.items():
        result = future.result()
        if key == 'audio':
            transcript, transcript_conf = result
        elif key == 'image':
            img = result
```
**Explanation:**
**Lines 145-147:** Default values set karta hai

**Line 149:** ThreadPoolExecutor banata hai (2 workers)

**Lines 150-154:** Tasks submit karta hai
- Agar audio ho, toh transcription task submit
- Agar image ho, toh analysis task submit

**Lines 157-162:** Results collect karta hai
- Har task ka result wait karta hai
- Results ko correct variables mein assign karta hai
- **Key Point:** Dono tasks simultaneously run hote hain (50% faster!)

**Lines 164-172: Multimodal Assessment**
```python
assessment = get_multimodal_assessment(
    image_summary=img["summary"],
    image_conf=img["confidence"],
    transcript=transcript,
    transcript_conf=transcript_conf,
    patient_id=patient_id,
    llm_client=llm_client,
)
```
**Explanation:**
- Image aur transcript ko combine karke assessment banata hai
- LLM client optional hai (fallback available)
- Patient history bhi include hoti hai

**Lines 174-181: Session State**
```python
session_state = {
    "image_summary": img["summary"],
    "image_conf": img["confidence"],
    "transcript": transcript,
    "transcript_conf": transcript_conf,
    "patient_id": patient_id,
    "history_summary": assessment.get("history_summary"),
}
```
**Explanation:**
- Session data store karta hai
- Chat functionality ke liye use hota hai

**Lines 183-189: Return Result**
```python
return {
    "transcript": transcript,
    "fusion_result": assessment["fusion_result"],
    "action_result": assessment["action_result"],
    "history_summary": assessment["history_summary"],
    "session_state": session_state,
}
```
**Explanation:**
- Complete result return karta hai
- UI ko sabhi data milta hai

---

## Workflow (काम कैसे होता है)

1. **Input Receive** - Audio aur image file paths receive hote hain
2. **Parallel Processing** - Dono tasks simultaneously start hote hain:
   - Audio transcription (Thread 1)
   - Image analysis (Thread 2)
3. **Results Wait** - Dono tasks complete hone ka wait karta hai
4. **Assessment** - Multimodal assessment generate hota hai
5. **State Save** - Session state update hota hai
6. **Return** - Complete result return hota hai

---

## Performance Optimization (Performance Improvements)

### Parallel Processing Benefits
- **Sequential**: Audio (3s) + Image (4s) = 7 seconds
- **Parallel**: max(Audio, Image) = 4 seconds
- **Speedup**: ~40-50% faster!

### Model Selection
- **STT**: `whisper-large-v3-turbo` - Fast transcription
- **Vision**: `llama-3.2-90b-vision-preview` - Fast vision model

---

## Error Handling (Error कैसे Handle होते हैं)

1. **No Audio** - Default message return hota hai
2. **No Image** - Default summary return hota hai
3. **API Key Missing** - Error message return hota hai
4. **API Failure** - Fallback logic use hota hai
5. **Thread Failure** - Exception catch hota hai, default values use hote hain

---

## Dependencies (जरूरी Libraries)

- `concurrent.futures` - Parallel processing
- `brain_of_the_doctor` - Image analysis
- `voice_of_the_patient` - Audio transcription

---

## Usage Example (कैसे Use करें)

```python
from app import api_local
from brain_of_the_doctor import GroqLLMClient

# LLM client banayein
llm_client = GroqLLMClient(api_key="your_key")

# Record submit karein
result = api_local.submit_record(
    audio_filepath="patient_audio.mp3",
    image_filepath="medical_image.jpg",
    patient_id="patient123",
    llm_client=llm_client
)

# Results access karein
print(result["transcript"])
print(result["fusion_result"]["preliminary_diagnosis"])
print(result["action_result"]["triage_action"])
```

---

## Integration (कहाँ Use होता है)

Yeh function `gradio_app.py` mein use hoti hai:
```python
result = api_local.submit_record(
    audio_filepath=audio_filepath,
    image_filepath=image_filepath,
    patient_id=patient_id or None,
    llm_client=llm_client,
)
```

---

## Key Features (मुख्य विशेषताएं)

1. **Parallel Processing** - Fast execution
2. **Error Resilience** - Fallback mechanisms
3. **Flexible Input** - Audio ya image dono optional
4. **Session Management** - State maintain karta hai
5. **LLM Optional** - Offline mode support

