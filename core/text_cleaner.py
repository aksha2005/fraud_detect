"""
core/text_cleaner.py
Adversarial text normalization.
- Strips zero-width Unicode characters used by scammers to bypass keyword filters.
- Normalizes common Leetspeak / homoglyph substitutions to plain ASCII equivalents.
This runs BEFORE the 4-engine analysis pipeline so every engine sees clean text.
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Zero-width & invisible Unicode characters used to evade filters
# ---------------------------------------------------------------------------
_ZERO_WIDTH_CHARS = re.compile(
    r"[\u200b\u200c\u200d\u200e\u200f\u00ad\ufeff\u2060\u2061\u2062\u2063\u2064]"
)

# ---------------------------------------------------------------------------
# Leetspeak / homoglyph map  (most common scammer substitutions)
# ---------------------------------------------------------------------------
_LEET_MAP = {
    # Latin homoglyphs
    "а": "a",  # Cyrillic а → Latin a
    "е": "e",  # Cyrillic е → Latin e
    "о": "o",  # Cyrillic о → Latin o
    "р": "p",  # Cyrillic р → Latin p
    "с": "c",  # Cyrillic с → Latin c
    "х": "x",  # Cyrillic х → Latin x
    "ι": "i",  # Greek ι → Latin i
    "α": "a",  # Greek alpha
    "β": "b",  # Greek beta
    "ρ": "p",  # Greek rho
    # Classic leetspeak digits → letters
    "0": "o",
    "1": "i",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "@": "a",
    "$": "s",
    "!": "i",
}

# We only apply digit/symbol → letter substitution INSIDE word-like tokens
# (not globally, to avoid mangling numeric amounts like ₹1500)
_LEET_WORD_PATTERN = re.compile(r"[A-Za-z0-9@$!α-ωА-яа-я]{3,}", re.UNICODE)


def _normalize_leet_token(token: str) -> str:
    """Replace leet characters in a token if it looks like a word (has letters)."""
    has_alpha = any(c.isalpha() for c in token)
    if not has_alpha:
        return token  # pure number — leave untouched
    result = []
    for ch in token:
        result.append(_LEET_MAP.get(ch, ch))
    return "".join(result)


def clean_text(text: str) -> str:
    """
    Full adversarial cleaning pipeline:
    1. Strip zero-width / invisible Unicode.
    2. Unicode NFC normalization (resolves composed accented characters).
    3. Normalize Leetspeak homoglyphs inside word tokens.
    Returns cleaned text preserving original spacing and punctuation.
    """
    # Step 1: Remove zero-width chars
    text = _ZERO_WIDTH_CHARS.sub("", text)

    # Step 1.5: Remove dots and spaces between single letters to catch O.T.P or K Y C
    # This regex looks for a single letter surrounded by word boundaries, followed by an optional dot/space, repeated.
    # Actually, a simpler approach is to strip dots that are sandwiched between letters:
    text = re.sub(r'(?i)(?<=\b[a-z])\s*\.\s*(?=[a-z]\b)', '', text)

    # Step 2: NFC normalization
    text = unicodedata.normalize("NFC", text)

    # Step 3: Normalize leet tokens
    text = _LEET_WORD_PATTERN.sub(
        lambda m: _normalize_leet_token(m.group(0)), text
    )

    return text
