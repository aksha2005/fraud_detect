"""
core/history_engine.py
FAISS-based community history lookup for similar scam reports.
Supports runtime report additions and exposes summary stats for the sidebar.
"""
import os
import json
import numpy as np
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Optional FAISS import
# ---------------------------------------------------------------------------
try:
    import faiss  # type: ignore
    _FAISS_OK = True
except ImportError:
    faiss = None
    _FAISS_OK = False

# ---------------------------------------------------------------------------
# Asset paths
# ---------------------------------------------------------------------------
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INDEX_PATH = os.path.join(_DATA_DIR, "history_index.faiss")
METADATA_PATH = os.path.join(_DATA_DIR, "history_metadata.json")

# ---------------------------------------------------------------------------
# Pre‑seeded metadata (10 records that ship with the repo)
# ---------------------------------------------------------------------------
_SEED_METADATA: List[Dict[str, Any]] = [
    {"text": "Congratulations! You have been selected for Internshala internship. Pay ₹1500 registration fee.", "summary": "Fake Internshala fee scam", "label": 1},
    {"text": "Your SBI account is blocked. Share OTP to update KYC immediately.", "summary": "SBI KYC OTP scam", "label": 1},
    {"text": "PM Scholarship of ₹50,000 approved. Pay ₹500 processing fee to release funds.", "summary": "Fake scholarship fee scam", "label": 1},
    {"text": "Congratulations! Your mobile won ₹5,00,000 lucky draw. Pay ₹999 processing fee.", "summary": "Lottery/prize scam", "label": 1},
    {"text": "Work from home: Earn ₹5000 daily liking YouTube videos. Pay ₹200 registration.", "summary": "WFH task scam", "label": 1},
    {"text": "Login to gooogle-security-login.com to avoid Gmail suspension.", "summary": "Typosquatted Google phishing", "label": 1},
    {"text": "TCS internship selected. Pay ₹2000 training fee to get your offer letter.", "summary": "Fake TCS offer letter scam", "label": 1},
    {"text": "KBC lottery: You won ₹25 lakh. Pay ₹3000 tax to claim reward.", "summary": "KBC lottery scam", "label": 1},
    {"text": "Dear student, your NSP scholarship status is available at scholarships.gov.in. Login with credentials.", "summary": "Legitimate NSP notification", "label": 0},
    {"text": "Your TCS NQT result is ready. Login to nextstep.tcs.com to check your score.", "summary": "Legitimate TCS result", "label": 0},
]


class UnifiedHistoryEngine:
    """In‑memory FAISS index of past scam reports.

    On first load the engine is pre‑seeded with 10 known scam/safe examples
    so the 'Community History' feature works immediately without requiring the
    user to run a separate build step.

    If FAISS is not installed the engine degrades gracefully: all methods
    return empty/safe defaults and the UI shows a helpful warning.
    """

    EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension

    def __init__(self, embedder=None):
        self.embedder = embedder          # sentence-transformers model (injected)
        self.metadata: List[Dict] = []
        self.index = None
        self._vectors: List[np.ndarray] = []   # mirror for persistence

        if _FAISS_OK:
            self.index = faiss.IndexFlatL2(self.EMBEDDING_DIM)
            self._try_load_disk()          # load pre-built index if available
            if len(self.metadata) == 0:
                self._seed()               # bootstrap with built-in examples

    # ------------------------------------------------------------------
    # Public stats
    # ------------------------------------------------------------------
    @property
    def total_reports(self) -> int:
        return len(self.metadata)

    @property
    def scam_count(self) -> int:
        return sum(1 for m in self.metadata if m.get("label") == 1)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        return _FAISS_OK and self.index is not None and len(self.metadata) > 0

    def add_report(self, text: str, label: int = 1) -> None:
        """Add a new report to the live index at runtime."""
        if not _FAISS_OK or self.embedder is None:
            # Can still store metadata even without FAISS (degraded mode)
            self.metadata.append({"text": text, "summary": text[:80], "label": label})
            return
        embedding = self.embedder.encode([text], show_progress_bar=False)
        vec = np.array(embedding, dtype=np.float32)
        if self.index is None:
            self.index = faiss.IndexFlatL2(self.EMBEDDING_DIM)
        self.index.add(vec)
        self.metadata.append({"text": text, "summary": text[:80], "label": label})

    def search_and_explain(self, text: str, k: int = 5) -> list[dict]:
        """Return the *top_k* most similar past reports."""
        if not self.is_available() or self.embedder is None:
            return []
        embedding = self.embedder.encode([text], show_progress_bar=False)
        query = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        distances, indices = self.index.search(query, k)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            entry = self.metadata[idx]
            similarity = max(0.0, 1.0 - np.sqrt(dist) / 2.0)
            results.append({
                "text": entry.get("text", ""),
                "summary": entry.get("summary", ""),
                "score": round(float(similarity) * 100, 1),
                "label": entry.get("label", 0),
            })
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _seed(self) -> None:
        """Populate index with built-in seed records."""
        if self.embedder is not None:
            for item in _SEED_METADATA:
                self.add_report(item["text"], item["label"])
        else:
            rng = np.random.default_rng(seed=42)
            for item in _SEED_METADATA:
                vec = rng.standard_normal((1, self.EMBEDDING_DIM)).astype(np.float32)
                faiss.normalize_L2(vec)
                self.index.add(vec)
                self.metadata.append({
                    "text":    item["text"],
                    "summary": item["summary"],
                    "label":   item["label"],
                })

    def _try_load_disk(self) -> None:
        """Load pre-built index from disk if present."""
        if not os.path.exists(INDEX_PATH) or not os.path.exists(METADATA_PATH):
            return
        try:
            disk_index = faiss.read_index(INDEX_PATH)
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                disk_meta = json.load(f)
            if disk_index.ntotal == len(disk_meta):
                self.index = disk_index
                self.metadata = disk_meta
        except Exception:
            pass
