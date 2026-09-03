import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# 1. Environment check

print("1. Environment Check:")
try:
    import streamlit
    import faiss
    import sentence_transformers
    import sklearn
    print(" - Libraries streamlit, faiss, sentence_transformers, sklearn imported successfully.")
except ImportError as e:
    print(f" - Missing library: {e}")
    sys.exit(1)

# 2. Artifact Verification
print("\n2. Artifact Verification:")
if os.path.exists("models/semantic_classifier.pkl"):
    print(" - models/semantic_classifier.pkl exists.")
else:
    print(" - models/semantic_classifier.pkl NOT FOUND.")
    sys.exit(1)

# 3. Live test
print("\n3. Live Test:")
sys.path.insert(0, os.path.abspath("."))
from core.fraud_rules import analyze as rules_analyze
from core.campus_checker import CampusChecker
from core.scorer import ScoreBreakdown, compute_final_score

text = "Internshala Alert: Your internship requires a ₹2000 security deposit. Pay via UPI to confirm."

campus_checker = CampusChecker()
r = rules_analyze(text)
campus_result = campus_checker.check(text)

bd = ScoreBreakdown(
    rules_score=r["score"],
    rules_signals=r["signals"],
    campus_score=campus_result["total_score"],
    campus_findings=campus_result["findings"],
    has_image=False
)
bd = compute_final_score(bd)
print(f" - Text: '{text}'")
print(f" - Final Score: {bd.final_score}")
print(f" - Verdict Label: {bd.label}")
print(f" - Rules Score: {bd.rules_score}")
print(f" - Campus Score: {bd.campus_score}")
print(f" - Campus Findings: {bd.campus_findings}")
