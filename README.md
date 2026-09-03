# Campus Fraud Shield 🛡️

Detects scam messages targeting college students — internship fees, fake scholarships,
OTP fraud, lottery scams — using a 4-engine ensemble running 100% offline.

---

## System requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 4 GB | 8 GB |
| Disk | 2 GB free | 4 GB |
| CPU | Any modern | i5 / Ryzen 5+ |
| GPU | Not required | — |
| Internet | First run only | — |

---

## Setup (one time)

```bash
# 1. Clone / unzip the project
cd campus_fraud_shield

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Train the ML model (downloads ~80 MB model on first run, then offline)
python train/train_model.py
```

---

## Run

```bash
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Project structure

```
campus_fraud_shield/
├── app.py                      # Streamlit frontend
├── requirements.txt
├── core/
│   ├── ml_model.py             # SemanticScamClassifier (sentence-transformers)
│   ├── history_engine.py       # FAISS: search + explain + cluster
│   ├── campus_checker.py       # 4 expert domain checks (pure logic)
│   ├── rules_engine.py         # Keyword / pattern rules
│   ├── domain_checker.py       # URL / email domain analysis
│   └── scorer.py               # Weighted ensemble (35/30/20/15)
├── utils/
│   └── action_advisor.py       # Action cards + complaint generator
├── train/
│   └── train_model.py          # Train & save SemanticScamClassifier
├── data/
│   └── campus_entities.json    # 22 Indian entities with fee/contact policies
├── models/                     # Auto-created by train_model.py
│   ├── semantic_classifier.pkl
│   ├── training_embeddings.npy
│   └── training_texts.json
└── tests/
    └── test_smoke.py           # Smoke tests (no ML needed)
```

---

## Score weights

| Engine | Weight | What it checks |
|--------|--------|----------------|
| Rules engine | 35% | Keyword patterns, fee language, urgency, OTP |
| Domain check | 30% | URLs, shortlinks, free-email senders |
| Semantic AI | 20% | all-MiniLM-L6-v2 embeddings + LogisticRegression |
| Community | 15% | FAISS similarity vs previously reported scams |

---

## Running tests (no model needed)

```bash
python tests/test_smoke.py
# or
python -m pytest tests/
```

---

## Adding training data

Edit `train/train_model.py` → `TRAINING_DATA` list.
Each entry: `("message text", 1)` for scam, `("message text", 0)` for safe.
Re-run `python train/train_model.py` after adding samples.

---

## Entities covered

Internshala · Naukri · LinkedIn · NSP · PM Scholarship · UGC · AICTE ·
SBI · HDFC · ICICI · Paytm · PhonePe · Google Pay · IRCTC ·
LetsIntern · Unstop · HackerEarth · Wipro · TCS · Infosys · Cognizant · Accenture
