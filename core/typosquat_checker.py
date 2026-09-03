"""
core/typosquat_checker.py
Detects domains that imitate trusted domains (typosquatting).
"""

import Levenshtein

TRUSTED_DOMAINS = {
    "google.com",
    "gmail.com",
    "internshala.com",
    "naukri.com",
    "linkedin.com",
    "scholarships.gov.in",
    "sbi.co.in",
    "onlinesbi.sbi",
    "hdfcbank.com",
    "icicibank.com",
    "axisbank.com",
    "canarabank.com",
    "unionbankofindia.co.in",
    "paytm.com",
    "phonepe.com",
    "npci.org.in",
    "uidai.gov.in",
    "incometax.gov.in",
    "irctc.co.in",
    "unstop.com",
    "hackerearth.com",
    "tcs.com",
    "infosys.com",
    "wipro.com",
    "accenture.com",
    "microsoft.com",
    "amazon.in",
}

def normalize_domain(domain: str) -> str:
    """Normalize common leetspeak substitutions."""
    mapping = {
        '0': 'o',
        '1': 'l', # or 'i' but l is more common in typosquatting for l/i confusion
        '3': 'e',
        '5': 's',
        '@': 'a',
        '$': 's'
    }
    for k, v in mapping.items():
        domain = domain.replace(k, v)
    return domain

def check(domains: list[str]) -> dict:
    """
    Check a list of domains for typosquatting.
    Returns:
        {
            "score": float,
            "signals": list[{suspected_domain, possible_official_domain, similarity, reason}]
        }
    """
    signals = []
    total_score = 0.0
    
    for domain in domains:
        if domain in TRUSTED_DOMAINS:
            continue
            
        normalized = normalize_domain(domain)
        best_match = None
        highest_sim = 0.0
        
        for trusted in TRUSTED_DOMAINS:
            # Check for brand name embedding (e.g. sbi-verify.com)
            trusted_name = trusted.split('.')[0]
            if trusted_name in domain and len(domain) > len(trusted_name):
                # Don't flag if it's a subdomain of the trusted domain (handled by domain_checker/tldextract usually, but just in case)
                if not domain.endswith('.' + trusted):
                    signals.append({
                        "suspected_domain": domain,
                        "possible_official_domain": trusted,
                        "similarity": 100,
                        "reason": f"This link uses the word '{trusted_name}' but does not belong to the official {trusted} domain.",
                        "points": 85
                    })
                    total_score += 85
                    continue
            
            # Edit distance check
            distance = Levenshtein.distance(normalized, trusted)
            max_len = max(len(normalized), len(trusted))
            if max_len == 0:
                continue
            sim = (1 - (distance / max_len)) * 100
            
            if sim > highest_sim:
                highest_sim = sim
                best_match = trusted
                
        # If similarity is between 75% and 99%, it's likely typosquatting
        # Exclude low similarity and exact matches (handled above)
        if best_match and 75 <= highest_sim < 100:
            signals.append({
                "suspected_domain": domain,
                "possible_official_domain": best_match,
                "similarity": round(highest_sim, 1),
                "reason": f"'{domain}' looks suspiciously similar to '{best_match}'.",
                "points": 95
            })
            total_score += 95
            
    return {
        "score": min(100.0, total_score),
        "signals": signals
    }
