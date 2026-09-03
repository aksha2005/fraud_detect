"""
core/scorer.py
Weighted ensemble scorer combining all 7 engines.
Weights:
  rules_score: 0.22
  domain_score: 0.18
  typosquat_score: 0.20
  semantic_score: 0.15
  community_score: 0.10
  campus_score: 0.10
  qr_image_score: 0.05
If no QR/image is uploaded, the qr_image_score weight is redistributed proportionally to maintain 100% total weight.
"""

from dataclasses import dataclass, field

WEIGHTS_FULL = {
    "rules_score": 0.22,
    "domain_score": 0.18,
    "typosquat_score": 0.20,
    "semantic_score": 0.15,
    "community_score": 0.10,
    "campus_score": 0.10,
    "qr_image_score": 0.05,
}

WEIGHTS_NO_IMAGE = {
    "rules_score": 0.22 / 0.95,
    "domain_score": 0.18 / 0.95,
    "typosquat_score": 0.20 / 0.95,
    "semantic_score": 0.15 / 0.95,
    "community_score": 0.10 / 0.95,
    "campus_score": 0.10 / 0.95,
    "qr_image_score": 0.0,
}

@dataclass
class ScoreBreakdown:
    rules_score: float = 0.0
    rules_signals: list[dict] = field(default_factory=list)

    domain_score: float = 0.0
    domain_signals: list[dict] = field(default_factory=list)
    
    typosquat_score: float = 0.0
    typosquat_signals: list[dict] = field(default_factory=list)

    semantic_score: float = 0.0
    semantic_reason: str = ""
    semantic_examples: list[dict] = field(default_factory=list)

    community_score: float = 0.0
    community_matches: list[dict] = field(default_factory=list)

    campus_score: float = 0.0
    campus_findings: list[dict] = field(default_factory=list)
    
    qr_image_score: float = 0.0
    has_image: bool = False

    @property
    def final_score(self) -> float:
        """Calculate the final score with dynamic weight redistribution.
        Engines that return a score of 0 (including QR/Image when absent) have
        their weights removed and the remaining weights are normalised to sum to
        1.0. This ensures text‑only threats are not diluted by inactive engines.
        """
        # Start from the full weight set and zero‑out the QR weight if no image.
        base_weights = WEIGHTS_FULL.copy()
        if not self.has_image:
            base_weights["qr_image_score"] = 0.0

        # Map current engine scores.
        scores = {
            "rules_score": self.rules_score,
            "domain_score": self.domain_score,
            "typosquat_score": self.typosquat_score,
            "semantic_score": self.semantic_score,
            "community_score": self.community_score,
            "campus_score": self.campus_score,
            "qr_image_score": self.qr_image_score if self.has_image else 0.0,
        }

        # Reduce total weight for any engine that contributed a zero score.
        total_weight = sum(base_weights.values())
        for key, score in scores.items():
            if score == 0 and base_weights.get(key, 0) > 0:
                total_weight -= base_weights[key]
                base_weights[key] = 0.0

        # Normalise the remaining non‑zero weights to keep the sum at 1.0.
        if total_weight > 0:
            for k, w in base_weights.items():
                if w > 0:
                    base_weights[k] = w / total_weight

        raw = (
            self.rules_score * base_weights["rules_score"]
            + self.domain_score * base_weights["domain_score"]
            + self.typosquat_score * base_weights["typosquat_score"]
            + self.semantic_score * base_weights["semantic_score"]
            + self.community_score * base_weights["community_score"]
            + self.campus_score * base_weights["campus_score"]
            + self.qr_image_score * base_weights["qr_image_score"]
        )
        return round(min(100.0, raw), 1)
    

    @property
    def label(self) -> str:
        s = self.final_score
        if s >= 75:
            return "High Risk Scam"
        elif s >= 45:
            return "Suspicious"
        return "Likely Safe"

    @property
    def formula_string(self) -> str:
        weights = WEIGHTS_FULL if self.has_image else WEIGHTS_NO_IMAGE
        parts = [
            f"{self.rules_score:.0f}×{weights['rules_score']:.2f}",
            f"{self.domain_score:.0f}×{weights['domain_score']:.2f}",
            f"{self.typosquat_score:.0f}×{weights['typosquat_score']:.2f}",
            f"{self.semantic_score:.0f}×{weights['semantic_score']:.2f}",
            f"{self.community_score:.0f}×{weights['community_score']:.2f}",
            f"{self.campus_score:.0f}×{weights['campus_score']:.2f}"
        ]
        if self.has_image:
            parts.append(f"{self.qr_image_score:.0f}×{weights['qr_image_score']:.2f}")
            
        formula = " + ".join(parts)
        return f"final_score = {formula} = {self.final_score}"

def compute_final_score(breakdown: ScoreBreakdown) -> ScoreBreakdown:
    """Pass-through for the dataclass."""
    return breakdown
