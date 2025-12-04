# Fusion Service Documentation (app/services/fusion_service.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`fusion_service.py` yeh file image summary, transcript, aur history ko combine karke medical diagnosis aur treatment plan banati hai. Yeh file LLM optional hai - agar LLM na ho toh deterministic fallback use hota hai.

### Main Responsibilities (मुख्य जिम्मेदारियां)

1. **Data Fusion** - Image + Audio + History ko combine karna
2. **LLM Integration** - Optional LLM se advanced diagnosis
3. **Fallback Logic** - Offline mode ke liye deterministic diagnosis
4. **Confidence Calculation** - Result confidence score

---

## Line-by-Line Code Explanation

### Lines 1-20: Imports and Setup
```python
"""
Fusion service
==============
...
"""
from __future__ import annotations
import json
from typing import Any, Dict, Optional
from app.prompts.medical_agent_prompt import build_medical_agent_prompt
```
**Explanation:**
- Module description
- Type hints ke liye imports
- JSON parsing ke liye
- Medical prompt builder import

### Lines 23-34: Confidence Normalization
```python
def _normalise_conf(conf: Optional[float]) -> float:
    """Normalise confidence value to [0, 1]. Accepts 0–1 or 0–100 scales."""
    if conf is None:
        return 0.5
    try:
        value = float(conf)
    except (TypeError, ValueError):
        return 0.5
    if value <= 1.0:
        return max(0.0, min(1.0, value))
    # Assume it's a percentage
    return max(0.0, min(1.0, value / 100.0))
```
**Explanation:**
- Confidence value ko 0-1 range mein normalize karta hai
- Agar None ho, toh 0.5 return (default)
- Agar 0-1 range mein ho, toh as-is return
- Agar 0-100 range mein ho (percentage), toh divide by 100

### Lines 37-59: Simple Findings Extraction
```python
def _extract_simple_findings(text: str) -> Dict[str, bool]:
    """
    Extremely simple keyword‑based "fact extraction".
    ...
    """
    text_lower = (text or "").lower()
    findings = {
        "acne": any(k in text_lower for k in ["acne", "pimple", "pimples", "zit"]),
        "rash": "rash" in text_lower,
        "redness": "red" in text_lower or "inflamed" in text_lower,
        ...
    }
    return findings
```
**Explanation:**
- Text mein keywords search karta hai
- Medical conditions detect karta hai
- Boolean dictionary return karta hai
- Offline mode ke liye use hota hai

### Lines 62-264: Fallback Plan Function
```python
def _fallback_plan(
    image_summary: str,
    transcript: str,
    history_summary: Optional[str],
    img_conf: float,
    txt_conf: float,
) -> Dict[str, Any]:
    """Deterministic, very conservative offline diagnosis + plan."""
```
**Explanation:**
Yeh function LLM ke bina diagnosis deti hai (offline mode).

**Lines 70-71: Text Combination**
```python
combined_text = " ".join(filter(None, [image_summary, transcript]))
findings = _extract_simple_findings(combined_text)
```
- Image summary aur transcript ko combine karta hai
- Keywords extract karta hai

**Lines 74-96: Blister Detection**
```python
if findings["blister"] or (findings["foot"] and ("blister" in combined_text.lower() or "fluid" in combined_text.lower())):
    preliminary_diagnosis = "Friction blister on the plantar aspect of the foot..."
    recommended_treatment = "LIKELY CONDITION:\nFriction blister...\n\nCARE INSTRUCTIONS:\n1. Avoid popping..."
    medicine_constituents = [
        "Petroleum Jelly - Occlusive barrier for healing",
        "Bacitracin (500 units/g) - Ointment (optional if blister is drained)",
        ...
    ]
```
**Explanation:**
- Blister condition detect karta hai
- Specific diagnosis aur treatment plan deta hai
- Medicine constituents list karta hai

**Lines 97-117: Wart Detection**
```python
elif findings["wart"] or (findings["foot"] and ("wart" in combined_text.lower() or "verruca" in combined_text.lower() or "black dots" in combined_text.lower())):
    preliminary_diagnosis = "Plantar wart (verruca) on the foot..."
    recommended_treatment = "LIKELY CONDITION:\nPlantar wart (verruca)\n\nCARE INSTRUCTIONS:\n1. Apply Salicylic Acid..."
    medicine_constituents = [
        "Salicylic Acid (15-40%) - Topical solution/gel",
        ...
    ]
```
**Explanation:**
- Wart condition detect karta hai
- Black dots (thrombosed capillaries) check karta hai
- Salicylic acid treatment suggest karta hai

**Lines 118-138: Callus Detection**
```python
elif findings["callus"] or (findings["foot"] and ("callus" in combined_text.lower() or "thickened" in combined_text.lower())):
    preliminary_diagnosis = "Callus or corn on the foot..."
    recommended_treatment = "LIKELY CONDITION:\nCallus or corn...\n\nCARE INSTRUCTIONS:\n1. Soak foot..."
    medicine_constituents = [
        "Urea (20-40%) - Cream (for softening)",
        ...
    ]
```
**Explanation:**
- Callus/corn condition detect karta hai
- Urea cream suggest karta hai
- Mechanical debridement recommend karta hai

**Lines 139-158: Acne Detection**
```python
elif findings["acne"] or "acne" in (image_summary or "").lower():
    preliminary_diagnosis = "Acne‑like inflammatory spots..."
    recommended_treatment = "Step 1: Cleanse twice daily..."
    medicine_constituents = [
        "Benzoyl Peroxide (2.5-5%) - Gel/Cream",
        "Adapalene (0.1%) - Cream/Gel",
        ...
    ]
```
**Explanation:**
- Acne condition detect karta hai
- Multi-step treatment plan deta hai
- Topical medications suggest karta hai

**Lines 159-178: Rash Detection**
```python
elif findings["rash"]:
    preliminary_diagnosis = "A localized skin rash..."
    recommended_treatment = "Step 1: Identify and avoid the suspected irritant..."
    medicine_constituents = [
        "Hydrocortisone (1%) - Cream/Ointment",
        "Cetirizine (10mg) - Tablet (for itching)",
        ...
    ]
```
**Explanation:**
- Rash condition detect karta hai
- Irritant avoidance suggest karta hai
- Topical steroids aur antihistamines recommend karta hai

**Lines 179-198: Default Case**
```python
else:
    preliminary_diagnosis = "A minor‑appearing skin change..."
    recommended_treatment = "Step 1: Maintain gentle skincare routine..."
    medicine_constituents = [
        "Ceramides - Moisturizer",
        ...
    ]
```
**Explanation:**
- Generic case ke liye conservative approach
- Monitoring recommend karta hai
- Basic skincare suggest karta hai

**Lines 200-237: Safety Notes**
```python
# Set safety notes based on condition type
if findings["blister"] or (findings["foot"] and "blister" in combined_text.lower()):
    safety_notes = (
        "WARNING SIGNS — SEEK CARE IF:\n"
        "- Redness spreads beyond the lesion\n"
        "- Pus develops\n"
        ...
    )
elif findings["wart"] or (findings["foot"] and "wart" in combined_text.lower()):
    safety_notes = (
        "WARNING SIGNS — SEEK CARE IF:\n"
        "- Wart spreads or multiplies rapidly\n"
        ...
    )
else:
    safety_notes = (
        "WARNING SIGNS — SEEK CARE IF:\n"
        "- Rapidly spreading redness\n"
        ...
    )
```
**Explanation:**
- Condition-specific warning signs
- Red flags identify karta hai
- When to seek care batata hai

**Lines 239-253: Reasoning Generation**
```python
reasoning_bits = []
if findings["acne"]:
    reasoning_bits.append("The description suggests acne‑type spots.")
if findings["rash"]:
    reasoning_bits.append("There is mention of a rash.")
if findings["redness"]:
    reasoning_bits.append("Redness or inflammation is described.")
if not reasoning_bits:
    reasoning_bits.append("Findings sound mild and localized...")

reasoning = " ".join(reasoning_bits)
history_summary = history_summary or "No significant prior history recorded."
reasoning += f" Previous history: {history_summary}"
```
**Explanation:**
- Reasoning bits collect karta hai
- History summary add karta hai
- Complete reasoning string banata hai

**Lines 253-264: Confidence Calculation & Return**
```python
fusion_confidence = round((img_conf + txt_conf) / 2.0, 2)

return {
    "preliminary_diagnosis": preliminary_diagnosis,
    "reasoning": reasoning,
    "recommended_treatment": recommended_treatment,
    "medicine_constituents": medicine_constituents,
    "safety_notes": safety_notes,
    "fusion_confidence": fusion_confidence,
    "llm_raw_output": None,
    "simple_findings": findings,
}
```
**Explanation:**
- Average confidence calculate karta hai
- Complete result dictionary return karta hai

### Lines 267-365: Main Fuse Function
```python
def fuse(
    image_summary: str,
    image_conf: Optional[float],
    transcript: str,
    transcript_conf: Optional[float],
    history_summary: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
```
**Explanation:**
Yeh main function hai jo LLM use karke ya fallback se diagnosis deti hai.

**Lines 287-298: LLM Check**
```python
img_conf_n = _normalise_conf(image_conf)
txt_conf_n = _normalise_conf(transcript_conf)

# If no LLM client is configured, fall back immediately.
if llm_client is None:
    return _fallback_plan(
        image_summary=image_summary,
        transcript=transcript,
        history_summary=history_summary,
        img_conf=img_conf_n,
        txt_conf=txt_conf_n,
    )
```
**Explanation:**
- Confidence normalize karta hai
- Agar LLM na ho, toh directly fallback return karta hai

**Lines 300-304: Prompt Building**
```python
prompt = build_medical_agent_prompt(
    image_summary=image_summary,
    transcript=transcript,
    history_summary=history_summary,
)
```
**Explanation:**
- Medical prompt banata hai
- Sabhi information include karta hai

**Lines 309-340: LLM Call & Error Handling**
```python
try:
    raw_output = llm_client.generate(prompt)
    if isinstance(raw_output, dict):
        parsed = raw_output
    else:
        parsed = json.loads(str(raw_output))
except json.JSONDecodeError as e:
    # JSON parsing failed - log and fall back
    print(f"Warning: LLM response was not valid JSON. Error: {e}")
    result = _fallback_plan(...)
    result["llm_raw_output"] = raw_output
    return result
except Exception as e:
    # Any other problem with the LLM should gracefully fall back.
    print(f"Warning: LLM generation failed: {e}")
    result = _fallback_plan(...)
    result["llm_raw_output"] = raw_output if 'raw_output' in locals() else None
    return result
```
**Explanation:**
- LLM se response generate karta hai
- JSON parse karta hai
- Agar parse fail ho, toh fallback use karta hai
- Error handling ke saath graceful fallback

**Lines 342-365: Result Validation & Return**
```python
# Basic validation and fallback defaults for missing keys.
fallback = _fallback_plan(...)

def _get(key: str, default_key: str) -> Any:
    value = parsed.get(key)
    return value if value not in (None, "") else fallback[default_key]

result: Dict[str, Any] = {
    "preliminary_diagnosis": _get("preliminary_diagnosis", "preliminary_diagnosis"),
    "reasoning": _get("reasoning", "reasoning"),
    "recommended_treatment": _get("recommended_treatment", "recommended_treatment"),
    "medicine_constituents": _get("medicine_constituents", "medicine_constituents"),
    "safety_notes": _get("safety_notes", "safety_notes"),
    "fusion_confidence": fallback["fusion_confidence"],
    "llm_raw_output": raw_output,
    "simple_findings": fallback["simple_findings"],
}
return result
```
**Explanation:**
- Fallback plan generate karta hai (defaults ke liye)
- Helper function jo missing keys handle karta hai
- Complete result dictionary banata hai
- LLM output aur fallback findings dono include karta hai

---

## Workflow (काम कैसे होता है)

1. **Input Receive** - Image summary, transcript, history receive hoti hai
2. **LLM Check** - Agar LLM client ho, toh use karta hai
3. **Prompt Build** - Medical prompt banata hai
4. **LLM Call** - LLM se diagnosis generate karta hai
5. **Parse & Validate** - JSON parse karke validate karta hai
6. **Fallback** - Agar fail ho, toh deterministic fallback use karta hai
7. **Return** - Complete diagnosis aur treatment plan return karta hai

---

## Key Features (मुख्य विशेषताएं)

1. **Dual Mode** - LLM mode aur offline fallback mode
2. **Error Resilience** - Multiple fallback layers
3. **Condition Detection** - Multiple medical conditions support
4. **Structured Output** - Consistent result format
5. **Confidence Scoring** - Result confidence calculate karta hai

---

## Dependencies (जरूरी Libraries)

- `json` - JSON parsing
- `app.prompts.medical_agent_prompt` - Prompt builder

---

## Usage Example (कैसे Use करें)

```python
from app.services.fusion_service import fuse
from brain_of_the_doctor import GroqLLMClient

# LLM client banayein
llm_client = GroqLLMClient(api_key="your_key")

# Fusion karein
result = fuse(
    image_summary="Photo shows a wart on foot with black dots",
    image_conf=0.85,
    transcript="I have a wart on my foot",
    transcript_conf=0.75,
    history_summary="Previous visit: similar wart",
    llm_client=llm_client
)

print(result["preliminary_diagnosis"])
print(result["recommended_treatment"])
```

