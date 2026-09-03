"""
train/train_model.py
Train the SemanticScamClassifier on labelled data from CSV.
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from core.ml_model import SemanticScamClassifier

DATA_FILE = Path(__file__).parent.parent / "data" / "training_data.csv"

def main() -> None:
    print("=" * 60)
    print("Campus Fraud Shield - Model Training")
    print("=" * 60)
    
    if not DATA_FILE.exists():
        print(f"Error: {DATA_FILE} not found.")
        return

    df = pd.read_csv(DATA_FILE)
    texts = df["text"].tolist()
    labels = df["label"].tolist()

    print(f"\nTotal samples: {len(texts)} ({sum(labels)} scam, {len(labels)-sum(labels)} safe)")
    print("\nLoading SentenceTransformer (all-MiniLM-L6-v2)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    print("Model loaded.")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.25, random_state=42, stratify=labels
    )

    print(f"\nTraining on {len(X_train)} samples, evaluating on {len(X_test)}...")
    clf = SemanticScamClassifier(embedder=embedder)
    clf.fit(X_train, y_train)

    # Evaluate
    test_embeddings = embedder.encode(X_test)
    preds = clf.classifier.predict(test_embeddings)
    print("\nClassification Report:")
    print(classification_report(y_test, preds, target_names=["SAFE", "SCAM"]))

    # Save
    clf.save()
    print("\nTraining complete. Files saved to models/")
    print("  -> models/semantic_classifier.pkl")
    print("  -> models/training_embeddings.npy")
    print("  -> models/training_texts.json")

if __name__ == "__main__":
    main()
