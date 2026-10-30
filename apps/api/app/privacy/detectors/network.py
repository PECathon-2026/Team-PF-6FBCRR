"""Network IP address detectors (IPv4 and IPv6)."""
import ipaddress
import re
from typing import List, Tuple

IPV4_REGEX = re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b')
IPV6_REGEX = re.compile(r'(?i)\b(?:[0-9a-f]{1,4}:){7}[0-9a-f]{1,4}\b|\b(?:[0-9a-f]{1,4}:){1,7}:[0-9a-f]{1,4}\b')

def detect_ips(text: str) -> List[Tuple[int, int, str, float, str]]:
    """Detects valid IPv4 and IPv6 addresses."""
    results = []
    
    # IPv4
    for match in IPV4_REGEX.finditer(text):
        ip_str = match.group(0)
        try:
            ip_obj = ipaddress.IPv4Address(ip_str)
            # Filter out obvious false positives like 0.0.0.0 or single digit version strings like 1.2.3.4
            if ip_str.startswith("0."):
                continue
            is_private = ip_obj.is_private
            confidence = 0.95
            reason = f"IPv4 Address ({'Internal / Private' if is_private else 'Public'})"
            results.append((match.start(), match.end(), ip_str, confidence, reason))
        except ValueError:
            pass
            
    # IPv6
    for match in IPV6_REGEX.finditer(text):
        ip_str = match.group(0)
        try:
            ipaddress.IPv6Address(ip_str)
            results.append((match.start(), match.end(), ip_str, 0.98, "IPv6 Address"))
        except ValueError:
            pass
            
    return results
