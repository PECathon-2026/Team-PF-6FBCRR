"""Email address and phone number detectors."""
import re
from typing import List, Tuple

EMAIL_REGEX = re.compile(
    r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b'
)

# International and Indian phone numbers:
# Indian: +91 9876543210, 09876543210, 98765-43210, (91) 9876543210
# International: +1-555-123-4567, etc.
PHONE_REGEX = re.compile(
    r'(?<!\w)(?:(?:\+91|91|0)?[-\s]?[6-9]\d{4}[-\s]?\d{5}|\+\d{1,3}[-\s.]?\(?\d{1,4}\)?[-\s.]?\d{3,4}[-\s.]?\d{3,4})(?!\w)'
)

def detect_emails(text: str) -> List[Tuple[int, int, str, float, str]]:
    """Detects RFC-compliant email addresses."""
    results = []
    for match in EMAIL_REGEX.finditer(text):
        results.append((
            match.start(),
            match.end(),
            match.group(0),
            0.99,
            "Standard email address pattern"
        ))
    return results

def detect_phones(text: str) -> List[Tuple[int, int, str, float, str]]:
    """Detects phone numbers with format and context analysis."""
    results = []
    for match in PHONE_REGEX.finditer(text):
        raw_val = match.group(0).strip()
        digits = re.sub(r'\D', '', raw_val)
        
        # Avoid short strings or order IDs
        if len(digits) < 10 or len(digits) > 15:
            continue
            
        # Context verification
        window_start = max(0, match.start() - 30)
        window_end = min(len(text), match.end() + 30)
        context = text[window_start:window_end].lower()
        has_phone_context = any(k in context for k in ["phone", "tel", "mobile", "call", "sms", "contact", "+91", "cell"])
        
        # Confidence logic
        if raw_val.startswith('+') or has_phone_context:
            confidence = 0.95
        elif len(digits) == 10 and digits[0] in "6789":  # Standard Indian mobile
            confidence = 0.90
        else:
            confidence = 0.75
            
        results.append((
            match.start(),
            match.end(),
            raw_val,
            confidence,
            "Telephone / mobile number pattern" + (" with contextual indicator" if has_phone_context else "")
        ))
    return results
