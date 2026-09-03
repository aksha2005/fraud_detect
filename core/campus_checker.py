"""
core/campus_checker.py
Class wrapper for campus entity policy checking.
"""
import os
import json
from typing import Dict, List

_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "campus_entities.json")

class CampusChecker:
    """Loads campus entity policies and provides a ``check`` method.

    The ``check`` method returns a dictionary with ``total_score`` (0‑100) and
    ``findings`` – a list of dicts containing ``entity``, ``reason`` and a
    ``score`` contribution.
    """

    def __init__(self):
        self.entities = {}
        if os.path.exists(_DATA_PATH):
            with open(_DATA_PATH, "r", encoding="utf-8") as f:
                self.entities = json.load(f).get("entities", {})
        else:
            # Fallback – empty policy set.
            self.entities = {}

    def check(self, text: str) -> Dict:
        """Analyse *text* for campus‑specific scam patterns.

        Scoring is simple: each matched keyword adds 15 points (capped at 100).
        """
        lowered = text.lower()
        total_score = 0
        findings: List[Dict] = []
        for entity, info in self.entities.items():
            matched_kw = None
            for kw in info.get("keywords", []):
                if kw.lower() in lowered:
                    matched_kw = kw
                    break
            if matched_kw:
                has_fee = any(fkw in lowered for fkw in ["fee", "deposit", "pay", "charge", "registration", "processing"])
                pts = 35 if (has_fee and info.get("fee_policy")) else 15
                reason = info.get("fee_policy_label") if (has_fee and info.get("fee_policy_label")) else f"Detected policy keyword '{matched_kw}' for {info.get('display_name', entity)}."
                total_score += pts
                findings.append({
                    "entity": entity,
                    "reason": reason,
                    "score": pts,
                })

        total_score = min(100, total_score)
        return {"total_score": total_score, "findings": findings}
