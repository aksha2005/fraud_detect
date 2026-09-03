"""
utils/action_advisor.py
Generates actionable advice and pre-filled complaint text.
"""
import datetime

def get_action(final_score: float, label: str, text: str, entities: dict = None) -> dict:
    """Returns advice based on the final label."""
    if entities is None:
        entities = {}
    if label in ("High Risk Scam", "SCAM"):
        return {
            "category": "scam",
            "title": "🚨 Do NOT interact. This is a scam.",
            "steps": [
                "Do NOT pay any money or transfer funds.",
                "Do NOT share any OTP, PIN, password, or banking details.",
                "Do NOT click on any links provided in the message.",
                "Block the sender immediately.",
                "Take screenshots of the entire conversation/message.",
                "Warn your friends/college group about this specific scam."
            ],
            "helpline": "1930",
            "online_report": "https://cybercrime.gov.in"
        }
    elif label == "Suspicious":
        return {
            "category": "suspicious",
            "title": "⚠️ Proceed with caution. This looks suspicious.",
            "steps": [
                "Do not share personal details yet.",
                "Verify the claim ONLY through the official website (type it in your browser manually).",
                "Do not use contact numbers or links provided in this message.",
                "Ask a placement officer, teacher, or trusted adult before responding."
            ]
        }
    else:
        return {
            "category": "safe",
            "title": "✅ This appears to be safe.",
            "steps": [
                "The message patterns look legitimate.",
                "However, still open official websites manually instead of clicking links if you are unsure.",
                "Never share OTPs or passwords with anyone, even if the message is safe."
            ]
        }



def generate_complaint_text(final_score: float, label: str, text: str, entities: dict = None, breakdown: dict = None) -> str:
    """Generates a pre-filled complaint text for cybercrime.gov.in."""
    if entities is None:
        entities = {}
    if breakdown is None:
        breakdown = {}
    if label not in ("High Risk Scam", "SCAM"):
        return None

        
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    amount_str = ", ".join(entities.get("amounts", [])) or "None specified"
    phone_str = ", ".join(entities.get("phones", [])) or "None found"
    url_str = ", ".join(entities.get("urls", [])) or "None found"
    email_str = ", ".join(entities.get("emails", [])) or "None found"
    upi_str = ", ".join(entities.get("upis", [])) or "None found"
    
    # Determine scam category broadly
    category = "Online Financial Fraud / Phishing"
    if "internship" in text.lower() or "job" in text.lower():
        category = "Fake Job / Internship Fraud"
    elif "scholarship" in text.lower():
        category = "Fake Scholarship Scheme Fraud"
    elif "otp" in text.lower() or "bank" in text.lower():
        category = "Banking / KYC OTP Fraud"
    elif "lottery" in text.lower() or "prize" in text.lower():
        category = "Lottery / Prize Scam"

    # Get top reasons
    reasons = []
    if breakdown.get("rules_signals"):
        reasons.extend([s["label"] for s in breakdown["rules_signals"][:2]])
    if breakdown.get("domain_signals"):
        reasons.extend([s["label"] for s in breakdown["domain_signals"][:1]])
    if breakdown.get("typosquat_signals"):
        reasons.extend([s["reason"] for s in breakdown["typosquat_signals"][:1]])
        
    top_reasons = "\n- ".join(reasons) if reasons else "Suspicious patterns detected by AI analysis."
    if reasons:
        top_reasons = "- " + top_reasons

    complaint = f"""I received a suspicious/fraudulent message on {date_str}.

Scam type: {category}
Risk score: {final_score}/100
Amount requested: {amount_str}
Phone/contact used: {phone_str}
URL found: {url_str}
Email found: {email_str}
UPI ID found: {upi_str}

Message/QR/screenshot content:
"{text}"

Reason for suspicion:
{top_reasons}

The message appears to be asking students for money, OTP, personal details, or payment through a suspicious link/contact. Please register this complaint and investigate.
"""
    return complaint
