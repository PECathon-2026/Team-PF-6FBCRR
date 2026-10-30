"""Secret tokens, API keys, JWTs, and private key detectors."""
import math
import re
from typing import List, Tuple
from app.models import SensitiveCategory

# Well-known API key prefixes
PREFIX_PATTERNS = [
    (re.compile(r'(?i)\bBearer\s+([A-Za-z0-9_\-\.]{16,})\b'), "HTTP Bearer authorization token"),
    (re.compile(r'\b(sk-[a-zA-Z0-9_\-]{20,})\b'), "OpenAI / standard secret key prefix (sk-)"),
    (re.compile(r'\b(ghp_[a-zA-Z0-9]{36})\b'), "GitHub Personal Access Token (ghp_)"),
    (re.compile(r'\b(gho_[a-zA-Z0-9]{36})\b'), "GitHub OAuth Access Token (gho_)"),
    (re.compile(r'\b(ak_[a-zA-Z0-9]{16,})\b'), "API Access Key prefix (ak_)"),
    (re.compile(r'\b(key-[a-zA-Z0-9]{16,})\b'), "API Key prefix (key-)"),
    (re.compile(r'\b(xox[baprs]-[0-9a-zA-Z-]{10,})\b'), "Slack API token"),
]

# JSON Web Token: header.payload.signature
JWT_REGEX = re.compile(r'\b(ey[A-Za-z0-9_\-]{10,}\.ey[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]+)\b')

# PEM Private Key block
PEM_PRIVATE_KEY_REGEX = re.compile(
    r'-----BEGIN\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----[\s\S]+?-----END\s+(?:RSA\s+|EC\s+|DSA\s+|OPENSSH\s+)?PRIVATE\s+KEY-----'
)

def _shannon_entropy(s: str) -> float:
    """Computes Shannon entropy of string."""
    if not s:
        return 0.0
    prob = [float(s.count(c)) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in prob)

def detect_secrets(text: str) -> List[Tuple[int, int, str, SensitiveCategory, float, str]]:
    """
    Detects API keys, authorization tokens, JWTs, PEM blocks, and high-entropy secret values.
    Returns: List of (start, end, val, category, confidence, reason)
    """
    results = []
    
    # 1. PEM Private Keys
    for match in PEM_PRIVATE_KEY_REGEX.finditer(text):
        results.append((
            match.start(),
            match.end(),
            match.group(0),
            SensitiveCategory.PRIVATE_KEY,
            1.0,
            "Cryptographic PEM private key block"
        ))
        
    # 2. JWTs
    for match in JWT_REGEX.finditer(text):
        results.append((
            match.start(1),
            match.end(1),
            match.group(1),
            SensitiveCategory.JWT,
            0.99,
            "Signed JSON Web Token (JWT)"
        ))
        
    # 3. Prefixed API keys
    for pattern, description in PREFIX_PATTERNS:
        for match in pattern.finditer(text):
            val = match.group(1) if match.lastindex else match.group(0)
            start = match.start(1) if match.lastindex else match.start()
            end = match.end(1) if match.lastindex else match.end()
            results.append((
                start,
                end,
                val,
                SensitiveCategory.API_KEY,
                0.98,
                description
            ))
            
    # 4. High-entropy candidate strings near secret context keywords
    secret_labels = ["api_key", "apikey", "secret", "token", "auth_token", "private_key", "access_key"]
    kv_regex = re.compile(r'(?i)\b([a-z_]{3,15})\s*[:=]\s*["\']?([A-Za-z0-9_\-]{20,})["\']?')
    for match in kv_regex.finditer(text):
        key = match.group(1).lower()
        val = match.group(2)
        if any(lbl in key for lbl in secret_labels):
            entropy = _shannon_entropy(val)
            if entropy > 3.2:
                results.append((
                    match.start(2),
                    match.end(2),
                    val,
                    SensitiveCategory.API_KEY,
                    0.94,
                    f"High-entropy secret token under key '{key}' (entropy: {entropy:.2f})"
                ))
                
    return results
