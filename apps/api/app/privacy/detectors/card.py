"""Credit and debit card detector with Luhn verification and CVV detection."""
import re
from typing import List, Tuple
from .luhn import validate_luhn

# 13 to 19 digits formatted with spaces, dashes, or plain digits
CARD_REGEX = re.compile(r'(?<!\d)(?:4\d{3}|5[1-5]\d{2}|6011|65\d{2}|3[47]\d{2}|35\d{2}|60\d{2})[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,7}(?!\d)')
GENERIC_NUM_CANDIDATE = re.compile(r'(?<!\d)(\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{1,7})(?!\d)')

# CVV: 3-4 digits with explicit CVV/CVC context
CVV_CONTEXT_REGEX = re.compile(r'(?i)(?:cvv|cvc|security\s*code|card\s*code|cvn|cid)\s*[:=]?\s*([0-9]{3,4})(?!\d)')

def detect_cards(text: str) -> List[Tuple[int, int, str, float, str]]:
    """
    Detects credit/debit card numbers using regex pattern + Luhn checksum validation.
    Returns list of (start, end, matched_text, confidence, reason).
    """
    results = []
    
    # 1. Major card brand patterns + Luhn
    for match in CARD_REGEX.finditer(text):
        raw_val = match.group(0)
        clean_num = re.sub(r'[-\s]', '', raw_val)
        if validate_luhn(clean_num):
            results.append((
                match.start(),
                match.end(),
                raw_val,
                0.99,
                f"Valid payment card number (Luhn verified, {len(clean_num)} digits)"
            ))
            
    # 2. Generic numeric sequences (13-19 digits) with Luhn
    for match in GENERIC_NUM_CANDIDATE.finditer(text):
        raw_val = match.group(1)
        clean_num = re.sub(r'[-\s]', '', raw_val)
        if 13 <= len(clean_num) <= 19 and validate_luhn(clean_num):
            # Avoid duplicate if already caught
            if not any(r[0] <= match.start() and match.end() <= r[1] for r in results):
                results.append((
                    match.start(1),
                    match.end(1),
                    raw_val,
                    0.95,
                    f"Payment card candidate (Luhn verified)"
                ))
                
    return results

def detect_cvv(text: str) -> List[Tuple[int, int, str, float, str]]:
    """
    Detects CVV/CVC security codes when accompanied by contextual keywords.
    """
    results = []
    for match in CVV_CONTEXT_REGEX.finditer(text):
        results.append((
            match.start(1),
            match.end(1),
            match.group(1),
            0.95,
            "Card security verification code (CVV/CVC)"
        ))
    return results
