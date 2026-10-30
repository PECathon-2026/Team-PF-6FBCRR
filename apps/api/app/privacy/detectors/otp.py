"""One-Time Password (OTP) detector strictly requiring verification context."""
import re
from typing import List, Tuple

# OTP context keywords
OTP_CONTEXT_TERMS = [
    "otp", "verification code", "one time password", "security code",
    "2fa", "two-factor", "passcode", "auth code", "sms code", "pin",
    "enter code", "verify"
]

OTP_CANDIDATE_REGEX = re.compile(r'(?<!\d)(\d{4,8})(?!\d)')

def detect_otp(text: str) -> List[Tuple[int, int, str, float, str]]:
    """
    Detects 4-8 digit OTPs only when surrounded by explicit OTP/verification context.
    Avoids false positives on years (e.g. 2026), prices, zip codes, or counts.
    """
    results = []
    text_lower = text.lower()
    
    for match in OTP_CANDIDATE_REGEX.finditer(text):
        val = match.group(1)
        
        # Check window around match
        window_start = max(0, match.start() - 40)
        window_end = min(len(text), match.end() + 40)
        surrounding = text_lower[window_start:window_end]
        
        # Exclude obvious non-OTP patterns: e.g. dates/years, dollar amounts
        if surrounding.startswith("$") or surrounding.startswith("€") or surrounding.startswith("₹"):
            continue
        if re.search(r'(?:year|copyright|©|\b19\d{2}\b|\b20\d{2}\b)', surrounding) and len(val) == 4:
            # Check if this 4-digit is actually a year
            if int(val) in range(1950, 2050) and not any(k in surrounding for k in ["otp", "code", "pin", "2fa"]):
                continue
                
        # Find explicit OTP indicator
        matched_term = next((term for term in OTP_CONTEXT_TERMS if term in surrounding), None)
        if matched_term:
            results.append((
                match.start(1),
                match.end(1),
                val,
                0.96,
                f"Numeric verification passcode under '{matched_term}' context"
            ))
            
    return results
