"""Aadhaar detector with Verhoeff checksum validation and masked format handling."""
import re
from typing import List, Tuple
from app.models import SensitiveCategory
from .verhoeff import validate_verhoeff

# Matches 12 digits with optional spaces or dashes
AADHAAR_REGEX = re.compile(r'(?<!\d)([2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4})(?!\d)')
# Matches masked Aadhaar: XXXX XXXX 1234 or **** **** 1234
MASKED_AADHAAR_REGEX = re.compile(r'(?i)(?<![a-z0-9])([x*]{4}[-\s]?[x*]{4}[-\s]?\d{4})(?![a-z0-9])')

def detect_aadhaar(text: str) -> List[Tuple[int, int, str, float, str]]:
    """
    Detects Aadhaar numbers in text.
    Returns list of (start, end, matched_text, confidence, reason).
    """
    results = []
    
    # 1. Unmasked Aadhaar numbers
    for match in AADHAAR_REGEX.finditer(text):
        raw_val = match.group(1)
        digits_only = re.sub(r'[-\s]', '', raw_val)
        if len(digits_only) == 12:
            # First digit of Aadhaar cannot be 0 or 1
            if digits_only[0] in '01':
                continue
            is_valid_verhoeff = validate_verhoeff(digits_only)
            confidence = 0.98 if is_valid_verhoeff else 0.40
            reason = "Aadhaar format with valid Verhoeff checksum" if is_valid_verhoeff else "Aadhaar candidate (invalid checksum)"
            
            # In strict mode or when checksum passes, report span
            if is_valid_verhoeff:
                results.append((match.start(1), match.end(1), raw_val, confidence, reason))
    
    # 2. Masked Aadhaar format
    for match in MASKED_AADHAAR_REGEX.finditer(text):
        raw_val = match.group(1)
        results.append((
            match.start(1),
            match.end(1),
            raw_val,
            0.95,
            "Masked Aadhaar format (XXXX-XXXX-NNNN)"
        ))
        
    return results
