"""
Fusion service
==============

Light‑weight multimodal fusion for:
- image summary
- transcript
- optional history summary

LLM calls are entirely optional: pass an object with ``generate(prompt: str)``
to enable them, otherwise this module falls back to deterministic heuristics
so the app can run fully offline.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.prompts.medical_agent_prompt import build_medical_agent_prompt


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


def _extract_simple_findings(text: str) -> Dict[str, bool]:
    """
    Extremely simple keyword‑based "fact extraction".

    This is deterministic and intentionally conservative – it just helps
    drive a reasonable offline heuristic when no LLM is configured.
    """
    text_lower = (text or "").lower()
    findings = {
        "acne": any(k in text_lower for k in ["acne", "pimple", "pimples", "zit"]),
        "rash": "rash" in text_lower,
        "redness": "red" in text_lower or "inflamed" in text_lower,
        "itch": "itch" in text_lower or "itchy" in text_lower,
        "pain": "pain" in text_lower or "tender" in text_lower,
        "fever": "fever" in text_lower,
        "trauma": any(k in text_lower for k in ["injury", "trauma", "hit", "fall"]),
        "chronic": any(k in text_lower for k in ["months", "years", "chronic"]),
        "blister": any(k in text_lower for k in ["blister", "fluid-filled", "friction"]),
        "wart": any(k in text_lower for k in ["wart", "verruca", "plantar wart"]),
        "callus": any(k in text_lower for k in ["callus", "thickened skin", "corn"]),
        "foot": any(k in text_lower for k in ["foot", "plantar", "sole", "heel", "toe"]),
    }
    return findings


def _fallback_plan(
    image_summary: str,
    transcript: str,
    history_summary: Optional[str],
    img_conf: float,
    txt_conf: float,
) -> Dict[str, Any]:
    """Deterministic, very conservative offline diagnosis + plan."""
    combined_text = " ".join(filter(None, [image_summary, transcript]))
    findings = _extract_simple_findings(combined_text)

    # Check for foot lesions (blisters, warts, calluses)
    if findings["blister"] or (findings["foot"] and ("blister" in combined_text.lower() or "fluid" in combined_text.lower())):
        preliminary_diagnosis = (
            "Friction blister on the plantar aspect of the foot (intact or torn)."
        )
        recommended_treatment = (
            "LIKELY CONDITION:\n"
            "Friction blister on plantar surface\n\n"
            "CARE INSTRUCTIONS:\n"
            "1. Avoid popping the blister unless it is very large or painful. Intact blisters heal faster and protect underlying skin.\n"
            "2. If draining is necessary (large, painful blister), use sterile technique: clean area, sterilize needle with alcohol, make small puncture at edge, gently press fluid out, apply petroleum jelly and sterile bandage.\n"
            "3. Apply Petroleum Jelly (Vaseline) as an occlusive barrier to promote healing. Evidence shows Vaseline heals blisters better than antibiotics in most cases with no allergy risk.\n"
            "4. If blister is open/drained, optionally apply Bacitracin (500 units/g) ointment to prevent infection, then cover with sterile non-stick bandage.\n"
            "5. Consider hydrocolloid blister plaster/dressing (contains Carboxymethylcellulose) to protect and speed healing.\n"
            "6. Use donut-shaped moleskin or padding around (not on) the blister to reduce pressure.\n"
            "7. Wear well-cushioned, properly fitting shoes to avoid recurrence.\n"
            "8. For pain, take Ibuprofen (400mg) or Paracetamol (500-1000mg) as needed (optional)."
        )
        medicine_constituents = [
            "Petroleum Jelly - Occlusive barrier for healing",
            "Bacitracin (500 units/g) - Ointment (optional if blister is drained)",
            "Hydrocolloid Dressing Components (Carboxymethylcellulose) - Blister protection",
            "Ibuprofen (400mg) - Pain relief (optional)"
        ]
    elif findings["wart"] or (findings["foot"] and ("wart" in combined_text.lower() or "verruca" in combined_text.lower() or "black dots" in combined_text.lower())):
        preliminary_diagnosis = (
            "Plantar wart (verruca) on the foot, characterized by rough surface and possible black dots (thrombosed capillaries)."
        )
        recommended_treatment = (
            "LIKELY CONDITION:\n"
            "Plantar wart (verruca)\n\n"
            "CARE INSTRUCTIONS:\n"
            "1. Apply Salicylic Acid (15-40%) topical solution/gel daily to the wart, covering surrounding healthy skin with petroleum jelly.\n"
            "2. Soak foot in warm water for 10-15 minutes before application to soften the wart.\n"
            "3. Gently file away dead skin with pumice stone or emery board after soaking.\n"
            "4. Consider duct tape occlusion therapy as adjunct: cover wart with duct tape, remove weekly, soak and file, repeat.\n"
            "5. Avoid picking or cutting the wart to prevent spread.\n"
            "6. Wear clean socks and avoid walking barefoot in public areas.\n"
            "7. Treatment typically takes 4-12 weeks. If no improvement, consider cryotherapy or professional removal."
        )
        medicine_constituents = [
            "Salicylic Acid (15-40%) - Topical solution/gel",
            "Petroleum Jelly - Protective barrier",
            "Duct tape - Occlusion therapy (adjunct)"
        ]
    elif findings["callus"] or (findings["foot"] and ("callus" in combined_text.lower() or "thickened" in combined_text.lower())):
        preliminary_diagnosis = (
            "Callus or corn on the foot, characterized by thickened, hardened skin."
        )
        recommended_treatment = (
            "LIKELY CONDITION:\n"
            "Callus or corn on plantar surface\n\n"
            "CARE INSTRUCTIONS:\n"
            "1. Soak foot in warm water for 10-15 minutes to soften thickened skin.\n"
            "2. Gently file away dead skin with pumice stone or emery board after soaking.\n"
            "3. Apply Urea (20-40%) cream daily to soften and moisturize.\n"
            "4. Use Salicylic Acid (10-20%) topical solution if needed for persistent calluses.\n"
            "5. Apply petroleum jelly and wear clean socks to keep area moisturized.\n"
            "6. Use donut padding or moleskin to reduce pressure on the affected area.\n"
            "7. Wear properly fitting, well-cushioned shoes to prevent recurrence."
        )
        medicine_constituents = [
            "Urea (20-40%) - Cream (for softening)",
            "Salicylic Acid (10-20%) - Topical solution",
            "Petroleum Jelly - Moisturizing barrier"
        ]
    elif findings["acne"] or "acne" in (image_summary or "").lower():
        preliminary_diagnosis = (
            "Acne‑like inflammatory spots on the skin, likely mild to moderate acne vulgaris."
        )
        recommended_treatment = (
            "Step 1: Cleanse twice daily with a gentle non‑comedogenic cleanser containing salicylic acid (2%). "
            "Step 2: Apply benzoyl peroxide (2.5-5%) gel or cream once daily in the evening, starting with lower concentration. "
            "Step 3: Alternatively or in combination, apply adapalene (0.1%) cream at night. "
            "Step 4: Use a non‑comedogenic moisturizer and broad‑spectrum sunscreen (SPF 30+) during the day. "
            "Step 5: Avoid picking, squeezing, or excessive scrubbing. Treatment typically shows improvement in 4-8 weeks. "
            "If no improvement after 8-12 weeks, consider adding topical clindamycin or consulting a dermatologist."
        )
        medicine_constituents = [
            "Benzoyl Peroxide (2.5-5%) - Gel/Cream",
            "Adapalene (0.1%) - Cream/Gel",
            "Salicylic Acid (2%) - Cleanser/Toner",
            "Clindamycin (1%) - Topical Solution (if needed)",
            "Niacinamide (4-5%) - Serum (supportive)",
            "Azelaic Acid (15-20%) - Cream (alternative)"
        ]
    elif findings["rash"]:
        preliminary_diagnosis = (
            "A localized skin rash that may represent irritant dermatitis, allergic contact dermatitis, or atopic dermatitis."
        )
        recommended_treatment = (
            "Step 1: Identify and avoid the suspected irritant or allergen immediately. "
            "Step 2: Gently cleanse the area with lukewarm water and a mild, fragrance-free cleanser. "
            "Step 3: Apply a thin layer of hydrocortisone (1%) cream or ointment twice daily for 5-7 days maximum. "
            "Step 4: Use fragrance-free emollients/moisturizers (containing ceramides or colloidal oatmeal) 2-3 times daily. "
            "Step 5: Apply cool compresses if itching is severe. Take oral antihistamines (cetirizine or loratadine) if needed for itching. "
            "Step 6: Monitor for signs of infection (increasing redness, pus, warmth). If rash worsens or persists beyond 2 weeks, seek medical evaluation."
        )
        medicine_constituents = [
            "Hydrocortisone (1%) - Cream/Ointment",
            "Cetirizine (10mg) - Tablet (for itching)",
            "Loratadine (10mg) - Tablet (alternative antihistamine)",
            "Ceramides - Moisturizer",
            "Colloidal Oatmeal - Soothing cream",
            "Dimethicone - Barrier cream"
        ]
    else:
        preliminary_diagnosis = (
            "A minor‑appearing skin change that is likely benign but requires careful monitoring and evaluation."
        )
        recommended_treatment = (
            "Step 1: Maintain gentle skincare routine with mild, fragrance-free products. "
            "Step 2: Apply a basic emollient moisturizer twice daily to keep skin hydrated. "
            "Step 3: Avoid harsh soaps, exfoliants, or new skincare products. "
            "Step 4: Protect the area from sun exposure with SPF 30+ sunscreen. "
            "Step 5: Monitor closely for changes in: size, shape, color, texture, pain, itching, or bleeding. "
            "Step 6: Document with photos weekly. Seek in‑person dermatological evaluation if: lesion grows rapidly, changes color significantly, becomes painful, bleeds, or if you have concerns. "
            "If unchanged after 4-6 weeks, consider professional evaluation for definitive diagnosis."
        )
        medicine_constituents = [
            "Ceramides - Moisturizer",
            "Glycerin - Hydrating cream",
            "Dimethicone - Barrier protection",
            "Zinc Oxide (SPF 30+) - Sunscreen",
            "Gentle cleansers (pH balanced, fragrance-free)"
        ]

    # Set safety notes based on condition type
    if findings["blister"] or (findings["foot"] and "blister" in combined_text.lower()):
        safety_notes = (
            "WARNING SIGNS — SEEK CARE IF:\n"
            "- Redness spreads beyond the lesion\n"
            "- Pus develops\n"
            "- Severe pain increases\n"
            "- Fever occurs\n"
            "- You have diabetes and wound healing is slow\n\n"
            "SPECIAL PRECAUTIONS:\n"
            "- Avoid Neomycin if you have allergies (use Petroleum Jelly instead)\n"
            "- If diabetic, monitor closely for slow healing or signs of infection\n"
            "- Keep area clean and dry, change bandages daily"
        )
    elif findings["wart"] or (findings["foot"] and "wart" in combined_text.lower()):
        safety_notes = (
            "WARNING SIGNS — SEEK CARE IF:\n"
            "- Wart spreads or multiplies rapidly\n"
            "- Severe pain or bleeding occurs\n"
            "- Signs of infection (redness, pus, warmth)\n"
            "- Wart does not improve after 12 weeks of treatment\n\n"
            "SPECIAL PRECAUTIONS:\n"
            "- Avoid picking or cutting wart to prevent spread\n"
            "- Do not share towels or footwear\n"
            "- If diabetic or immunocompromised, seek professional care"
        )
    else:
        safety_notes = (
            "WARNING SIGNS — SEEK CARE IF:\n"
            "- Rapidly spreading redness\n"
            "- Severe pain\n"
            "- High fever\n"
            "- Signs of systemic infection\n"
            "- Difficulty breathing or facial swelling\n\n"
            "SPECIAL PRECAUTIONS:\n"
            "- Monitor for changes in size, color, or symptoms\n"
            "- Seek in-person evaluation if condition worsens or persists"
        )

    reasoning_bits = []
    if findings["acne"]:
        reasoning_bits.append("The description suggests acne‑type spots.")
    if findings["rash"]:
        reasoning_bits.append("There is mention of a rash.")
    if findings["redness"]:
        reasoning_bits.append("Redness or inflammation is described.")
    if not reasoning_bits:
        reasoning_bits.append("Findings sound mild and localized without strong red‑flag keywords.")

    reasoning = " ".join(reasoning_bits)
    history_summary = history_summary or "No significant prior history recorded."
    reasoning += f" Previous history: {history_summary}"

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


def fuse(
    image_summary: str,
    image_conf: Optional[float],
    transcript: str,
    transcript_conf: Optional[float],
    history_summary: Optional[str] = None,
    llm_client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Fuse image + transcript (+ history) into a structured assessment.

    Returns a dict with at least these keys:
    - preliminary_diagnosis
    - reasoning
    - recommended_treatment
    - medicine_constituents
    - safety_notes
    - fusion_confidence
    - llm_raw_output
    """
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

    prompt = build_medical_agent_prompt(
        image_summary=image_summary,
        transcript=transcript,
        history_summary=history_summary,
    )

    raw_output: Optional[str] = None
    parsed: Dict[str, Any]

    try:
        raw_output = llm_client.generate(prompt)
        if isinstance(raw_output, dict):
            parsed = raw_output
        else:
            # Try to parse JSON
            parsed = json.loads(str(raw_output))
    except json.JSONDecodeError as e:
        # JSON parsing failed - log and fall back
        print(f"Warning: LLM response was not valid JSON. Error: {e}")
        print(f"Raw output preview: {str(raw_output)[:200]}...")
        result = _fallback_plan(
            image_summary=image_summary,
            transcript=transcript,
            history_summary=history_summary,
            img_conf=img_conf_n,
            txt_conf=txt_conf_n,
        )
        result["llm_raw_output"] = raw_output
        return result
    except Exception as e:
        # Any other problem with the LLM should gracefully fall back.
        print(f"Warning: LLM generation failed: {e}")
        result = _fallback_plan(
            image_summary=image_summary,
            transcript=transcript,
            history_summary=history_summary,
            img_conf=img_conf_n,
            txt_conf=txt_conf_n,
        )
        result["llm_raw_output"] = raw_output if 'raw_output' in locals() else None
        return result

    # Basic validation and fallback defaults for missing keys.
    fallback = _fallback_plan(
        image_summary=image_summary,
        transcript=transcript,
        history_summary=history_summary,
        img_conf=img_conf_n,
        txt_conf=txt_conf_n,
    )

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


