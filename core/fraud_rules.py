'''core/fraud_rules.py
Fraud rules engine implementing keyword detection and scoring.
'''

import re
from typing import List, Dict

# High‑risk keyword groups and their point values (as per spec)
_KEYWORD_SCORES = {
    # fee / payment related
    r"\b(registration fee|joining fee|training fee|security deposit|refundable deposit|pay\s*₹?|payment|processing fee)\b": 35,
    r"\b(upi\s*payment|pay\s*via\s*upi|upi://)\b": 35,
    # OTP / password / PIN
    r"\b(otp|one[-\s]?time[-\s]?password|pin|password|pwd|cvv|account\s*number\s*verify)\b": 45,
    # urgent / limited time
    r"\b(urgent|immediate|asap|24\s*hours|limited|only\s*\d+\s*slots)\b": 15,
    # prize / lottery
    r"\b(lottery|prize|winner|won|congratulations|lucky|claim reward)\b": 35,
    # selection / interview bypass
    r"\b(selected|selection|direct selection|no interview|selected without interview)\b": 30,
    # work‑from‑home / part‑time scams
    r"\b(work from home|wfh|earn\s*\d+|part[-\s]?time|quick money)\b": 25,
    # short link detection (handled elsewhere but also contributes)
    r"\b(bit\.ly|tinyurl\.com|goo\.gl|t\.co|ow\.ly)\b": 25,
    # communication channel only (WhatsApp/Telegram)
    r"\b(whatsapp only|telegram only)\b": 20,
    # free email usage as official contact
    r"\b(@gmail\.com|@yahoo\.com)\b": 20,
    # KYC / account block
    r"\b(account\s*blocked|kyc\s*update|verify\s*account)\b": 35,
    # Aadhaar / PAN / bank details request
    r"\b(aadhaar|pan|bank\s*details|account\s*number)\b": 30,
}

# Compile regexes once for performance
_COMPILED_PATTERNS = [(re.compile(pattern, re.IGNORECASE), points) for pattern, points in _KEYWORD_SCORES.items()]


def analyze(text: str) -> Dict:
    """Analyse ``text`` for scam‑related keywords.

    Returns a dict with ``score`` (0‑100 capped) and ``signals`` –
    a list of dicts ``{"label": str, "points": int}``.
    """
    signals: List[Dict] = []
    total = 0
    for regex, pts in _COMPILED_PATTERNS:
        if regex.search(text):
            # Use the matching keyword as label (first match)
            match = regex.search(text)
            label = match.group(0).strip()
            signals.append({"label": label, "points": pts})
            total += pts
    # Cap at 100
    total = min(100, total)
    return {"score": total, "signals": signals}
