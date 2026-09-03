"""
core/rules_engine.py
Keyword and pattern-based rule engine.
Returns a 0-100 score and list of matched signals with individual weights.
"""

import re

# Each rule: (pattern, score_contribution, human_label)
RULES: list[tuple] = [
    # High-weight scam signals
    (re.compile(r"\b(registration fee|joining fee|training fee|processing fee)\b", re.I), 35, "Registration/joining fee requested"),
    (re.compile(r"\b(otp|one.time.password)\b.*\b(share|send|give|enter)\b", re.I), 40, "OTP sharing requested"),
    (re.compile(r"\b(share|send|give).{0,20}\b(otp|pin|password)\b", re.I), 40, "Credential sharing requested"),
    (re.compile(r"\b(you (have|are) (won|selected|chosen)).{0,30}(pay|fee|deposit|send)\b", re.I), 38, "Prize/selection + payment combo"),
    (re.compile(r"\b(bit\.ly|tinyurl|goo\.gl|cutt\.ly|ow\.ly)\b", re.I), 20, "Shortened/suspicious link"),
    (re.compile(r"\b(24 hours?|48 hours?|urgent|immediately|act now|last chance)\b", re.I), 17, "Artificial urgency language"),
    (re.compile(r"\b(guaranteed|100%|assured)\b.{0,30}\b(job|internship|placement|income|earn)\b", re.I), 22, "Guaranteed job/income claim"),
    (re.compile(r"\b(work from home|wfh).{0,30}\b(earn|₹|income|daily|weekly)\b", re.I), 20, "WFH income offer"),
    (re.compile(r"\b(lottery|prize|lucky draw|lucky winner)\b", re.I), 25, "Lottery/prize claim"),
    (re.compile(r"@(gmail|yahoo|hotmail|outlook)\.com", re.I), 18, "Free email used as official contact"),
    (re.compile(r"\b(advance|deposit).{0,20}₹", re.I), 28, "Advance payment in INR required"),
    (re.compile(r"₹\s*[\d,]+.{0,20}\b(fee|charge|pay|deposit)\b", re.I), 25, "Specific INR amount + fee language"),
    # Medium-weight
    (re.compile(r"\bwhatsapp (only|contact|message)\b", re.I), 12, "WhatsApp-only contact"),
    (re.compile(r"\b(telegram|t\.me)\b", re.I), 10, "Telegram contact"),
    (re.compile(r"\b(click here|click the link|tap here)\b", re.I), 8, "Click-bait link language"),
    (re.compile(r"\b(verify your|confirm your).{0,20}(account|details|bank|card)\b", re.I), 18, "Account verification request"),
    (re.compile(r"\b(limited seats?|limited offer|only \d+ left)\b", re.I), 10, "Artificial scarcity"),
    # Low-weight contextual signals
    (re.compile(r"\b(earn ₹[\d,]+ (per|a) (day|week|month))\b", re.I), 15, "Specific daily/monthly earnings claim"),
    (re.compile(r"\b(no experience (needed|required)|freshers? (welcome|wanted))\b", re.I), 5, "No experience required"),
    (re.compile(r"\b(congratulations|you have been selected)\b", re.I), 8, "Unsolicited congratulations"),
]


def score(text: str) -> dict:
    """
    Run all rules against text.
    Returns: {score: float, signals: list[{label, points}]}
    """
    matched_signals = []
    total = 0.0

    for pattern, points, label in RULES:
        if pattern.search(text):
            matched_signals.append({"label": label, "points": points})
            total += points

    return {
        "score": min(100.0, round(total, 1)),
        "signals": matched_signals,
    }
