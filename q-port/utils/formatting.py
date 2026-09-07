"""
Formatting utilities for Q-PORT platform.
Provides human-readable Indian Rupee (₹) currency, percentages, scientific notation, and metric formatting.
"""

def format_inr(amount: float) -> str:
    """Formats number as Indian Rupee (e.g. ₹10,00,000.00)."""
    try:
        val = float(amount)
    except (ValueError, TypeError):
        return "₹0.00"

    is_negative = val < 0
    val = abs(val)
    s = f"{val:.2f}"
    integer_part, decimal_part = s.split(".")

    if len(integer_part) <= 3:
        formatted_int = integer_part
    else:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        pairs = []
        while len(remaining) > 2:
            pairs.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            pairs.append(remaining)
        pairs.reverse()
        formatted_int = ",".join(pairs) + "," + last_three

    prefix = "-" if is_negative else ""
    return f"₹{prefix}{formatted_int}.{decimal_part}"


def format_pct(val: float, decimals: int = 2) -> str:
    """Formats decimal as percentage string (e.g. 0.152 -> 15.20%)."""
    return f"{val * 100.0:.{decimals}f}%"


def format_sec(seconds: float) -> str:
    """Formats seconds with appropriate unit (ms vs s)."""
    if seconds < 0.001:
        return f"{seconds * 1000000:.1f} µs"
    elif seconds < 1.0:
        return f"{seconds * 1000:.1f} ms"
    else:
        return f"{seconds:.2f} s"
