"""
tests/test_smoke.py
Quick smoke tests — no ML model needed. Run with: python -m pytest tests/
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


from core.rules_engine import score as rules_score
from core.domain_checker import score as domain_score
from core.campus_checker import CampusChecker
from utils.action_advisor import get_action, generate_complaint_text


SCAM_TEXT = (
    "Congratulations! You have been selected for internship. "
    "Pay ₹1500 registration fee via bit.ly/pay-now. "
    "Contact: internship.hr@gmail.com. Urgent — 24 hours only."
)

SAFE_TEXT = (
    "Your Internshala application has been reviewed. "
    "The hiring team will contact you within 3 business days via your registered email."
)


def test_rules_engine_catches_scam():
    result = rules_score(SCAM_TEXT)
    assert result["score"] > 40, "Rules engine should flag scam text"
    assert len(result["signals"]) > 0


def test_rules_engine_safe_message():
    result = rules_score(SAFE_TEXT)
    assert result["score"] < 30, "Rules engine should not heavily flag safe text"


def test_domain_checker_catches_shortlink():
    result = domain_score(SCAM_TEXT)
    assert result["score"] > 0
    assert any("bit.ly" in s["value"].lower() for s in result["signals"])


def test_domain_checker_catches_free_email():
    result = domain_score(SCAM_TEXT)
    labels = [s["label"].lower() for s in result["signals"]]
    assert any("gmail" in l for l in labels)


def test_campus_checker_fee_violation():
    text = "Internshala internship selected. Pay ₹999 registration fee."
    checker = CampusChecker()
    result = checker.check(text)
    assert result["total_score"] > 0
    assert len(result["findings"]) > 0


def test_campus_checker_gov_scheme_fee():
    text = "PM Scholarship approved. Pay ₹500 processing fee to release funds."
    checker = CampusChecker()
    result = checker.check(text)
    assert result["total_score"] > 30


def test_campus_checker_gov_scheme_amount():
    text = "PM Scholarship of ₹1,00,000 per month approved for you."
    checker = CampusChecker()
    result = checker.check(text)
    assert result["total_score"] > 0  # amount exceeds real max


def test_action_advisor_returns_action():
    action = get_action(85.0, "SCAM", SCAM_TEXT)
    assert "steps" in action
    assert len(action["steps"]) > 0


def test_action_advisor_safe_message():
    action = get_action(10.0, "SAFE", SAFE_TEXT)
    assert action["category"] == "safe"


def test_complaint_text_extracts_values():
    text = (
        "Pay ₹1500 fee. Contact: 9876543210. "
        "Congratulations on your selection for internship."
    )
    complaint = generate_complaint_text(85.0, "SCAM", text)
    assert complaint is not None
    assert "9876543210" in complaint
    assert "₹1,500" in complaint or "1500" in complaint


def test_complaint_text_safe_returns_none():
    complaint = generate_complaint_text(10.0, "SAFE", SAFE_TEXT)
    assert complaint is None


if __name__ == "__main__":
    tests = [
        test_rules_engine_catches_scam,
        test_rules_engine_safe_message,
        test_domain_checker_catches_shortlink,
        test_domain_checker_catches_free_email,
        test_campus_checker_fee_violation,
        test_campus_checker_gov_scheme_fee,
        test_campus_checker_gov_scheme_amount,
        test_action_advisor_returns_action,
        test_action_advisor_safe_message,
        test_complaint_text_extracts_values,
        test_complaint_text_safe_returns_none,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            print(f"  ✓ {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__} ERROR: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
