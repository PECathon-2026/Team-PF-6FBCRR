"""Verhoeff checksum algorithm implementation for Aadhaar validation."""

# The multiplication table
_d = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# The permutation table
_p = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# The inverse table
_inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

def validate_verhoeff(number: str) -> bool:
    """Validates a number string using the Verhoeff algorithm."""
    clean = "".join(c for c in number if c.isdigit())
    if not clean:
        return False
    c = 0
    # Process digits in reverse order
    for i, item in enumerate(reversed(clean)):
        c = _d[c][_p[i % 8][int(item)]]
    return c == 0

def generate_verhoeff(number: str) -> str:
    """Generates the Verhoeff checksum digit for a number string."""
    clean = "".join(c for c in number if c.isdigit())
    c = 0
    for i, item in enumerate(reversed(clean)):
        c = _d[c][_p[(i + 1) % 8][int(item)]]
    return str(_inv[c])
