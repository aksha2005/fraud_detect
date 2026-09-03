'''core/domain_checker.py
Domain and link analysis engine.
''' 

import re
from urllib.parse import urlparse
import tldextract

# Short link domains and suspicious TLDs
SHORT_LINK_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "goo.gl",
    "t.co",
    "ow.ly",
    "short.link",
    "cutt.ly",
    "rb.gy",
    "tiny.cc",
    "is.gd",
}

SUSPICIOUS_TLDS = {"xyz", "top", "click", "loan", "work", "tk", "ml", "ga", "cf"}
FREE_HOSTING = {"blogspot.com", "wordpress.com", "wixsite.com", "sites.google.com"}

def _extract_urls(text: str) -> list[str]:
    # Simple URL regex (covers http(s) and www.)
    url_regex = re.compile(r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?)")
    return url_regex.findall(text)

def _analyze_url(url: str) -> dict:
    # Normalise URL
    if not url.startswith("http"):
        url = "http://" + url
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    # Remove www.
    if domain.startswith("www."):
        domain = domain[4:]
    result = {
        "original": url,
        "domain": domain,
        "short_link": domain in SHORT_LINK_DOMAINS,
        "suspicious_tld": any(domain.endswith('.' + tld) for tld in SUSPICIOUS_TLDS),
        "free_hosting": any(domain.endswith(host) for host in FREE_HOSTING),
        "https": parsed.scheme == "https",
        "has_ip": re.fullmatch(r"\d+\.\d+\.\d+\.\d+", domain) is not None,
    }
    return result

def check(text: str) -> dict:
    """Analyse all URLs found in *text*.
    Returns a dict with overall ``score`` (0‑100) and a list of ``signals``.
    """
    urls = _extract_urls(text)
    signals = []
    total = 0
    for u in urls:
        info = _analyze_url(u)
        # Assign points for each suspicious property
        if info["short_link"]:
            signals.append({"label": f"Short link detected: {info['domain']}", "points": 25, "value": info["domain"]})
            total += 25
        if not info["https"]:
            signals.append({"label": f"Non‑HTTPS link: {info['domain']}", "points": 10, "value": info["domain"]})
            total += 10
        if info["suspicious_tld"]:
            signals.append({"label": f"Suspicious TLD for {info['domain']}", "points": 15, "value": info["domain"]})
            total += 15
        if info["free_hosting"]:
            signals.append({"label": f"Free‑hosting domain: {info['domain']}", "points": 12, "value": info["domain"]})
            total += 12
        if info["has_ip"]:
            signals.append({"label": f"IP address URL: {info['domain']}", "points": 20, "value": info["domain"]})
            total += 20

    # Cap at 100
    total = min(100, total)
    return {"score": total, "signals": signals, "urls": urls}

score = check

