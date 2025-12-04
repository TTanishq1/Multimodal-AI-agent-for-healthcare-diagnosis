# Medical Agent Prompt Documentation (app/prompts/medical_agent_prompt.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`medical_agent_prompt.py` yeh file LLM ko medical diagnosis ke liye detailed prompt provide karti hai. Yeh prompt medical expert ko instruct karta hai ki kaise diagnosis aur treatment plan banana hai.

### Main Function: build_medical_agent_prompt

**Lines 156-179:** Function jo prompt build karta hai

```python
def build_medical_agent_prompt(
    image_summary: str,
    transcript: str,
    history_summary: Optional[str] = None,
) -> str:
```

**Explanation:**
- Template mein actual data fill karta hai
- Complete prompt string return karta hai

### Prompt Template Structure

**Lines 12-153:** Detailed prompt template

**Role Definition (Lines 14-25):**
- Medical doctor ka role define karta hai
- All medical specialties mention karta hai
- Comprehensive knowledge emphasize karta hai

**Context (Lines 27-33):**
- Image findings
- Patient symptoms
- Previous history

**Task (Lines 35-37):**
- JSON format mein assessment provide karna
- Evidence-based approach

**Critical Requirements (Lines 39-67):**
- Condition differentiation
- Visual findings matching
- Differential diagnosis

**Medication Requirements (Lines 69-103):**
- Active ingredients with dosages
- Formulation types
- All medications list karna

**Output Format (Lines 105-118):**
- JSON structure define karta hai
- Har field ka detailed description

**Quality Standards (Lines 120-140):**
- Specificity requirements
- Repetition avoidance
- Evidence-based recommendations

**Data Insertion (Lines 142-149):**
- `{image_summary}` - Image analysis
- `{transcript}` - Patient description
- `{history_summary}` - Previous visits

---

## Key Instructions

1. **Diagnosis Accuracy** - Visual findings match karna zaroori hai
2. **Condition Differentiation** - Similar conditions ko distinguish karna
3. **Medication Details** - Exact dosages aur formulations
4. **No Repetition** - Information repeat nahi karni
5. **JSON Only** - Pure JSON format, no markdown

---

## Usage
```python
from app.prompts.medical_agent_prompt import build_medical_agent_prompt

prompt = build_medical_agent_prompt(
    image_summary="Wart on foot with black dots",
    transcript="I have a wart on my foot",
    history_summary="Previous visit: similar condition"
)

# LLM ko prompt bhejein
response = llm_client.generate(prompt)
```

