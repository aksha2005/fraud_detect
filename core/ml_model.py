"""
core/ml_model.py
Semantic scam classifier using sentence-transformers + LogisticRegression.
Same model (all-MiniLM-L6-v2) shared with history_engine via st.cache_resource.
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from sklearn.linear_model import LogisticRegression

MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_PATH = MODEL_DIR / "semantic_classifier.pkl"
EMBEDDINGS_PATH = MODEL_DIR / "training_embeddings.npy"
TEXTS_PATH = MODEL_DIR / "training_texts.json"

class SemanticScamClassifier:
    """
    NLP engine combining SentenceTransformers + LogisticRegression classifier with heuristic fallbacks.
    """

    def __init__(self, embedder=None):
        self.embedder = embedder
        self.classifier = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
        self.is_trained = False
        self.training_embeddings = None
        self.training_texts = []
        self.training_labels = []

        self.urgency_kws = ['turant', 'abhi', 'last chance', 'expires today', 'within 24 hours', 'immediate action', "don't delay", 'urgent', 'immediately']
        self.fear_kws = ['account band', 'account blocked', 'legal notice', 'police case', 'penalty', 'suspended', 'arrested', 'kyc']
        self.greed_kws = ['free laptop', 'scholarship guaranteed', 'selected for internship', 'winner', 'prize', 'cashback 100%', 'earn daily', 'registration fee']

        self.load(embedder=embedder)

    def fit(self, X_train: list[str], y_train: list[int]) -> None:
        """Fit LogisticRegression on embeddings generated from X_train."""
        if self.embedder is None:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        embeddings = self.embedder.encode(X_train, show_progress_bar=False)
        self.classifier.fit(embeddings, y_train)
        self.is_trained = True
        self.training_texts = X_train
        self.training_labels = y_train
        self.training_embeddings = np.array(embeddings, dtype=np.float32)

    def predict_proba(self, text: str) -> tuple[float, str]:
        """Return (scam_score_0_to_100, human_readable_reason)."""
        if self.is_trained and self.classifier is not None and self.embedder is not None:
            try:
                emb = self.embedder.encode([text], show_progress_bar=False)
                probs = self.classifier.predict_proba(emb)[0]
                scam_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
                score = round(scam_prob * 100.0, 1)
                reason = f"Semantic AI Confidence: {score}% match with learned scam intent patterns."
                return score, reason
            except Exception:
                pass

        # Heuristic fallback if ML model is unavailable
        lower_text = text.lower()
        keyword_score = 0
        buckets_triggered = []

        if any(k in lower_text for k in self.urgency_kws):
            keyword_score += 15
            buckets_triggered.append("Urgency")
        if any(k in lower_text for k in self.fear_kws):
            keyword_score += 15
            buckets_triggered.append("Fear")
        if any(k in lower_text for k in self.greed_kws):
            keyword_score += 15
            buckets_triggered.append("Greed")

        score = min(100.0, float(keyword_score))
        reason = "Language Pattern Analysis: "
        if buckets_triggered:
            reason += f"Matched emotional triggers ({', '.join(buckets_triggered)})."
        else:
            reason += "No strong semantic scam patterns detected."

        return score, reason

    def get_similar_training_examples(self, text: str, n: int = 3) -> list[dict]:
        """Returns top n similar training examples with similarity % and labels."""
        if not self.is_trained or self.embedder is None or self.training_embeddings is None or len(self.training_texts) == 0:
            return []

        try:
            emb = self.embedder.encode([text], show_progress_bar=False)[0]
            # Compute cosine similarity
            norm_q = np.linalg.norm(emb)
            norm_train = np.linalg.norm(self.training_embeddings, axis=1)
            dot = np.dot(self.training_embeddings, emb)
            sims = dot / (norm_train * norm_q + 1e-8)

            top_indices = np.argsort(sims)[::-1][:n]
            results = []
            for idx in top_indices:
                sim_pct = round(max(0.0, float(sims[idx])) * 100.0, 1)
                lbl = self.training_labels[idx] if idx < len(self.training_labels) else 0
                results.append({
                    "text": self.training_texts[idx],
                    "label_str": "SCAM" if lbl == 1 else "SAFE",
                    "similarity": sim_pct,
                })
            return results
        except Exception:
            return []

    def save(self) -> None:
        """Save classifier model and training embeddings to models/ directory."""
        MODEL_DIR.mkdir(exist_ok=True, parents=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump({
                "classifier": self.classifier,
                "is_trained": self.is_trained,
                "training_labels": self.training_labels,
            }, f)
        if self.training_embeddings is not None:
            np.save(EMBEDDINGS_PATH, self.training_embeddings)
        if self.training_texts:
            with open(TEXTS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.training_texts, f, ensure_ascii=False, indent=2)

    def load(self, embedder=None) -> bool:
        """Load trained model artifacts from disk if available."""
        if embedder is not None:
            self.embedder = embedder

        if MODEL_PATH.exists():
            try:
                with open(MODEL_PATH, "rb") as f:
                    data = pickle.load(f)
                if isinstance(data, dict):
                    self.classifier = data.get("classifier", self.classifier)
                    self.is_trained = data.get("is_trained", True)
                    self.training_labels = data.get("training_labels", [])
                elif hasattr(data, "predict"):
                    self.classifier = data
                    self.is_trained = True
            except Exception:
                pass

        if EMBEDDINGS_PATH.exists():
            try:
                self.training_embeddings = np.load(EMBEDDINGS_PATH)
            except Exception:
                pass

        if TEXTS_PATH.exists():
            try:
                with open(TEXTS_PATH, "r", encoding="utf-8") as f:
                    self.training_texts = json.load(f)
            except Exception:
                pass

        return self.is_trained
