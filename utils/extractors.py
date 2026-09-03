"""
utils/extractors.py
Regex utilities to pull URLs, emails, phone numbers, UPI IDs, amounts.
"""

import re

# Amounts: ₹1500, Rs. 1500, INR 1500, 1500 rupees
AMOUNT_PATTERN = re.compile(r"(?:₹|rs\.?|inr)\s*([\d,]+)|([\d,]+)\s*(?:rupees|rs)", re.IGNORECASE)

# Phone numbers: +91 9876543210, 9876543210, 09876543210
PHONE_PATTERN = re.compile(r"(?:(?:\+|00)91[-\s]?)?[6-9]\d{9}")

# URLs
URL_PATTERN = re.compile(r"https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?")

# Emails
EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", re.IGNORECASE)

# UPI IDs: name@upi, name@ybl, name@okaxis, name@ibl, name@paytm
UPI_PATTERN = re.compile(r"[\w.-]+@(upi|ybl|okaxis|okicici|okhdfcbank|oksbi|ibl|axl|paytm|apairtel)", re.IGNORECASE)


def extract_all(text: str) -> dict:
    """Extracts all entities from text."""
    
    amounts = []
    for match in AMOUNT_PATTERN.finditer(text):
        amt = match.group(1) or match.group(2)
        if amt:
            # Clean commas and format
            clean_amt = amt.replace(",", "").strip()
            if clean_amt.isdigit():
                amounts.append(f"₹{int(clean_amt):,}")
                
    phones = [m.group(0) for m in PHONE_PATTERN.finditer(text)]
    urls = [m.group(0) for m in URL_PATTERN.finditer(text)]
    emails = [m.group(0) for m in EMAIL_PATTERN.finditer(text)]
    upis = [m.group(0) for m in UPI_PATTERN.finditer(text)]
    
    return {
        "amounts": list(set(amounts)),
        "phones": list(set(phones)),
        "urls": list(set(urls)),
        "emails": list(set(emails)),
        "upis": list(set(upis))
    }
