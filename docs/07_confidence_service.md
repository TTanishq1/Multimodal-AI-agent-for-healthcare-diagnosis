# Confidence Service Documentation (app/services/confidence_service.py)
## Hinglish में Complete Explanation

### Overview (समझाइश)
`confidence_service.py` yeh file confidence scores calculate karke triage decision leti hai. Yeh decide karti hai ki patient ko self-care, monitoring, ya in-person review chahiye.

### Main Function: compute_action

**Lines 22-70:** Main function jo confidence calculate karke triage action decide karti hai.

```python
def compute_action(
    fusion_conf: float,
    image_conf: Optional[float],
    transcript_conf: Optional[float],
    fused_findings: Optional[Dict[str, Any]],
    conflict_flag: bool = False,
) -> Dict[str, Any]:
```

**Explanation:**
- Multiple confidence scores ko combine karta hai
- Final confidence calculate karta hai
- Triage action decide karta hai

**Lines 38-39: Thresholds**
```python
low_th = _get_threshold("FUSION_CONFIDENCE_LOW", 0.55)
high_th = _get_threshold("FUSION_CONFIDENCE_HIGH", 0.8)
```
- Environment variables se thresholds leta hai
- Default: Low=0.55, High=0.8

**Lines 42-51: Normalization**
```python
def _norm(c: Optional[float]) -> float:
    if c is None:
        return fusion_conf
    try:
        v = float(c)
    except (TypeError, ValueError):
        return fusion_conf
    if v > 1.0:
        v = v / 100.0
    return max(0.0, min(1.0, v))
```
- Confidence values ko 0-1 range mein normalize karta hai
- Percentage values handle karta hai

**Lines 53-58: Aggregation**
```python
img_c = _norm(image_conf)
txt_c = _norm(transcript_conf)
signals = [fusion_conf, img_c, txt_c]
final_conf = sum(signals) / len(signals)
```
- Sabhi confidence scores ko average karta hai
- Simple averaging algorithm

**Lines 60-65: Triage Decision**
```python
if final_conf >= high_th and not conflict_flag:
    triage_action = "self_care_and_routine_followup"
elif final_conf >= low_th:
    triage_action = "monitor_closely_and_seek_care_if_worse"
else:
    triage_action = "recommend_in_person_review"
```
- High confidence (≥0.8): Self-care
- Medium confidence (≥0.55): Monitor closely
- Low confidence (<0.55): In-person review

**Return:** `{"final_confidence": float, "triage_action": str}`

---

## Workflow
1. Confidence scores normalize
2. Average calculate
3. Thresholds compare
4. Triage action decide
5. Result return

---

## Configuration
`.env` file mein:
- `FUSION_CONFIDENCE_LOW=0.55`
- `FUSION_CONFIDENCE_HIGH=0.8`

