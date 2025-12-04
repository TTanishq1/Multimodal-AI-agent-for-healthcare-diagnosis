"""
Confidence and triage decision service.

This keeps the policy very simple and data‑driven with environment
variables for thresholds, while remaining fully deterministic.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _get_threshold(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, default))
    except (TypeError, ValueError):
        value = default
    return max(0.0, min(1.0, value))


def compute_action(
    fusion_conf: float,
    image_conf: Optional[float],
    transcript_conf: Optional[float],
    fused_findings: Optional[Dict[str, Any]],
    conflict_flag: bool = False,
) -> Dict[str, Any]:
    """
    Compute confidence and triage action.

    Returns:
        {
          "final_confidence": float,
          "triage_action": str,
        }
    """
    low_th = _get_threshold("FUSION_CONFIDENCE_LOW", 0.55)
    high_th = _get_threshold("FUSION_CONFIDENCE_HIGH", 0.8)

    # Normalise sub‑confidences if they look like percentages.
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

    img_c = _norm(image_conf)
    txt_c = _norm(transcript_conf)

    # Simple aggregation: average all available signals.
    signals = [fusion_conf, img_c, txt_c]
    final_conf = sum(signals) / len(signals)

    if final_conf >= high_th and not conflict_flag:
        triage_action = "self_care_and_routine_followup"
    elif final_conf >= low_th:
        triage_action = "monitor_closely_and_seek_care_if_worse"
    else:
        triage_action = "recommend_in_person_review"

    return {
        "final_confidence": round(final_conf, 2),
        "triage_action": triage_action,
    }


