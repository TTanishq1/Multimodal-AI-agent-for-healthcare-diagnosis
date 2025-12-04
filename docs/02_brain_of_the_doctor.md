# Brain of the Doctor Documentation (brain_of_the_doctor.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`brain_of_the_doctor.py` yeh main brain hai jo LLM (Large Language Model) se baat karta hai aur medical images analyze karta hai. Yeh file Groq API ko use karke medical diagnosis provide karti hai.

### Main Responsibilities (मुख्य जिम्मेदारियां)

1. **LLM Client** - Groq API se baat karne ke liye wrapper
2. **Image Analysis** - Medical images ko analyze karta hai
3. **Multimodal Assessment** - Image + Audio + History ko combine karke assessment deta hai

---

## Line-by-Line Code Explanation

### Lines 1-3: Environment Setup
```python
# if you dont use pipenv uncomment the following:
from dotenv import load_dotenv
load_dotenv()
```
**Explanation:**
- `.env` file se environment variables load karta hai
- API keys access karne ke liye zaroori hai

### Lines 5-11: Module Description
```python
"""
Legacy multimodal image interface + new lightweight fusion wrapper.
...
"""
```
**Explanation:**
- File ka purpose explain karta hai
- Legacy code aur new fusion service dono support karta hai

### Lines 13-16: Standard Imports
```python
import base64
import os
from datetime import datetime
from typing import Any, Dict, Optional
```
**Explanation:**
- `base64` - Images ko encode karne ke liye (API ke liye)
- `os` - Environment variables access karne ke liye
- `datetime` - Timestamps generate karne ke liye
- `typing` - Type hints ke liye (code clarity ke liye)

### Lines 18-22: Groq Library Import
```python
try:
    # Optional – the app can run without Groq installed.
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Groq = None
```
**Explanation:**
- Groq library import karta hai
- Agar library install na ho, toh `Groq = None` set karta hai
- Yeh app ko offline mode mein bhi run karne deta hai

### Lines 24-26: Service Imports
```python
from app.services.fusion_service import fuse
from app.services.confidence_service import compute_action
from app.services.history_service import get_history_summary, save_visit
```
**Explanation:**
- `fuse` - Image aur transcript ko combine karta hai
- `compute_action` - Confidence calculate karke triage decision leta hai
- `get_history_summary`, `save_visit` - Patient history manage karta hai

### Line 29: API Key
```python
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
```
**Explanation:**
- Environment se Groq API key fetch karta hai
- Global variable hai jo baar-baar use hoti hai

### Lines 32-58: GroqLLMClient Class
```python
class GroqLLMClient:
    """
    Simple wrapper to make Groq compatible with fusion_service's llm_client interface.
    ...
    """
```
**Explanation:**
Yeh class Groq API ko use karke LLM calls handle karti hai.

**Lines 40-58: __init__ Method**
```python
def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
    if Groq is None:
        raise ValueError("Groq library is not installed")
    
    self.api_key = api_key or GROQ_API_KEY
    if not self.api_key:
        raise ValueError("GROQ_API_KEY must be set")
    
    self.client = Groq(api_key=self.api_key)
    self.model = model
```
**Explanation:**
- Constructor method jo client initialize karta hai
- API key validate karta hai
- Groq client banata hai
- Model name set karta hai (default: `llama-3.3-70b-versatile` - fast aur accurate)

**Lines 60-121: generate Method**
```python
def generate(self, prompt: str) -> str:
    """
    Generate response from prompt. Returns JSON string.
    """
    try:
        # Try with JSON mode first (if supported by model)
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a medical expert. Always respond with valid JSON only..."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.3,  # Lower temperature for more consistent, accurate responses
                max_tokens=1500,  # Limit tokens for faster responses
                response_format={"type": "json_object"}  # Force JSON output
            )
        except Exception:
            # Fallback if JSON mode not supported
            chat_completion = self.client.chat.completions.create(
                messages=[...],
                model=self.model,
                temperature=0.3,
                max_tokens=1500,
            )
```
**Explanation:**
- Prompt ko LLM ko bhejta hai
- Pehle JSON mode try karta hai (agar model support kare)
- Agar fail ho, toh normal mode use karta hai
- `temperature=0.3` - Low temperature se consistent responses milte hain
- `max_tokens=1500` - Response length limit (speed ke liye)

**Lines 107-119: Response Cleaning**
```python
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
```
**Explanation:**
- LLM ka response clean karta hai
- Markdown code blocks remove karta hai
- Pure JSON string return karta hai

### Lines 124-127: Image Encoding Function
```python
def encode_image(image_path: str) -> str:
    """Convert an image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
```
**Explanation:**
- Image file ko base64 string mein convert karta hai
- API ko image bhejne ke liye zaroori format
- Binary mode mein file read karta hai

### Lines 130-133: Default Constants
```python
QUERY_DEFAULT = "Is there something wrong with my face?"
MODEL_DEFAULT = "meta-llama/llama-4-maverick-17b-128e-instruct"
```
**Explanation:**
- Default query string (legacy code ke liye)
- Default model name (high accuracy ke liye)

### Lines 136-169: Image Analysis Function
```python
def analyze_image_with_query(query: str, model: str, encoded_image: str) -> str:
    """
    Backwards‑compatible Groq multimodal call.
    ...
    """
    if Groq is None:
        return "Image analysis model is not configured; using offline fallback description only."

    api_key = GROQ_API_KEY
    if not api_key or api_key == "your_groq_api_key_here" or api_key == "":
        raise ValueError("GROQ_API_KEY must be set in environment or .env file")
    
    client = Groq(api_key=api_key, timeout=30.0)  # Set timeout for faster failure
```
**Explanation:**
- Image analysis ke liye main function
- API key validate karta hai
- Client banata hai with timeout (30 seconds)

**Lines 151-162: Message Creation**
```python
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
```
**Explanation:**
- Multimodal message banata hai (text + image)
- Image ko base64 format mein embed karta hai
- Data URL format use karta hai

**Lines 163-169: API Call**
```python
chat_completion = client.chat.completions.create(
    messages=messages, 
    model=model,
    max_tokens=1000,  # Limit tokens for faster vision responses
    temperature=0.2  # Lower temperature for more focused responses
)
return chat_completion.choices[0].message.content
```
**Explanation:**
- Vision API call karta hai
- `max_tokens=1000` - Vision responses ke liye limit
- `temperature=0.2` - Very focused responses
- Response text return karta hai

### Lines 174-222: Multimodal Assessment Function
```python
def get_multimodal_assessment(
    image_summary: str,
    image_conf: float,
    transcript: str,
    transcript_conf: float,
    patient_id: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
```
**Explanation:**
Yeh main function hai jo sab kuch combine karta hai.

**Lines 190-199: History & Fusion**
```python
history_summary = get_history_summary(patient_id)

fusion_result = fuse(
    image_summary=image_summary,
    image_conf=image_conf,
    transcript=transcript,
    transcript_conf=transcript_conf,
    history_summary=history_summary,
    llm_client=llm_client,
)
```
**Explanation:**
- Patient ka previous history fetch karta hai
- `fuse()` function call karta hai jo sab kuch combine karta hai
- LLM client optional hai (agar na ho toh fallback use hota hai)

**Lines 201-207: Action Computation**
```python
action_result = compute_action(
    fusion_conf=fusion_result.get("fusion_confidence", 0.5),
    image_conf=image_conf,
    transcript_conf=transcript_conf,
    fused_findings=fusion_result.get("simple_findings"),
    conflict_flag=False,
)
```
**Explanation:**
- Confidence calculate karta hai
- Triage action decide karta hai (self-care, monitor, or in-person review)

**Lines 209-216: Visit Persistence**
```python
save_visit(
    patient_id=patient_id,
    transcript=transcript,
    image_summary=image_summary,
    fusion_result=fusion_result,
    timestamp=datetime.utcnow().isoformat(timespec="seconds"),
)
```
**Explanation:**
- Current visit ko database mein save karta hai
- Future visits ke liye history maintain karta hai
- Timestamp UTC format mein save hota hai

**Lines 218-222: Return Result**
```python
return {
    "fusion_result": fusion_result,
    "action_result": action_result,
    "history_summary": history_summary,
}
```
**Explanation:**
- Sabhi results return karta hai
- UI ko yeh data display karne ke liye milta hai

---

## Key Features (मुख्य विशेषताएं)

1. **LLM Integration** - Groq API se medical diagnosis
2. **Vision Analysis** - Medical images analyze karta hai
3. **Multimodal Fusion** - Image + Audio + History combine karta hai
4. **Offline Support** - LLM na ho toh bhi fallback se kaam karta hai
5. **History Management** - Patient history maintain karta hai

---

## Model Selection (Model कैसे Choose करें)

- **Speed Priority**: `llama-3.3-70b-versatile` (current default)
- **Accuracy Priority**: `meta-llama/llama-4-maverick-17b-128e-instruct`
- **Ultra Fast**: `llama-3.1-8b-instant`

---

## Error Handling (Error कैसे Handle होते हैं)

1. **API Key Missing** - ValueError raise hota hai
2. **Groq Library Missing** - Offline fallback use hota hai
3. **API Call Failure** - Exception catch karke fallback use hota hai
4. **JSON Parse Error** - Fallback plan use hota hai

---

## Dependencies (जरूरी Libraries)

- `groq` - Groq API client
- `base64` - Image encoding
- `app.services.*` - Internal services

---

## Usage Example (कैसे Use करें)

```python
from brain_of_the_doctor import get_multimodal_assessment, GroqLLMClient

# LLM client banayein
llm_client = GroqLLMClient(api_key="your_key")

# Assessment lein
result = get_multimodal_assessment(
    image_summary="Photo shows a wart on foot",
    image_conf=0.85,
    transcript="I have a wart on my foot",
    transcript_conf=0.75,
    patient_id="patient123",
    llm_client=llm_client
)

print(result["fusion_result"]["preliminary_diagnosis"])
```

