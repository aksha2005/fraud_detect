# 🛡️ Campus Fraud Shield

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B.svg)](https://streamlit.io/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-00599C.svg)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Campus Fraud Shield is an AI-powered, 100% offline cybersecurity tool designed to protect college students from campus-targeted scams, fake internships, scholarship fraud, and malicious links.**

---

## 📌 System Requirements

| Resource | Minimum | Recommended |
| :--- | :--- | :--- |
| **RAM** | 4 GB | 8 GB |
| **Disk** | 2 GB free | 4 GB |
| **CPU** | Any modern CPU | i5 / Ryzen 5+ |
| **GPU** | Not required | — |
| **Internet** | First run only (to download local weights) | Completely Offline |

---

## 🚀 Quick Start

```bash
# 1. Navigate to project folder
cd campus_fraud_shield

# 2. Create & activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Train the ML model (downloads ~80 MB model once, runs offline after)
python train/train_model.py

# 5. Launch the application
streamlit run app.py
