"""Indian Permanent Account Number (PAN) detector."""
import re
from typing import List, Tuple

# PAN structure: 5 uppercase letters, 4 digits, 1 uppercase letter
PAN_REGEX = re.compile(r'(?<![A-Za-z0-9])([A-Z]{5}[0-9]{4}[A-Z])(?![A-Za-z0-9])')
VALID_4TH_CHARS = set("PCHFATBLJG")

def detect_pan(text: str) -> List[Tuple[int, int, str, float, str]]:
    """
    Detects Indian PAN cards in text.
    Returns list of (start, end, matched_text, confidence, reason).
    """
    results = []
    for match in PAN_REGEX.finditer(text):
        pan_val = match.group(1)
        fourth_char = pan_val[3]
        
        # Check context keywords around match
        window_start = max(0, match.start() - 30)
        window_end = min(len(text), match.end() + 30)
        context = text[window_start:window_end].lower()
        has_context = any(k in context for k in ["pan", "tax", "income", "card", "identity", "kyc"])
        
        if fourth_char in VALID_4TH_CHARS:
            confidence = 0.95 if has_context else 0.85
            reason = f"PAN card format (category {fourth_char})" + (" with contextual keyword" if has_context else "")
        else:
            confidence = 0.65
            reason = "PAN card shape (uncommon 4th letter)"
            
        results.append((match.start(1), match.end(1), pan_val, confidence, reason))
        
    return results
