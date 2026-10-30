"""Luhn algorithm implementation for payment card validation."""

def validate_luhn(card_number: str) -> bool:
    """Validates a card number using the Luhn algorithm (mod 10)."""
    digits = [int(c) for c in card_number if c.isdigit()]
    if len(digits) < 12 or len(digits) > 19:
        return False
    
    checksum = 0
    # Process from right to left
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            if doubled > 9:
                doubled -= 9
            checksum += doubled
        else:
            checksum += d
            
    return (checksum % 10) == 0
