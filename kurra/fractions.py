"""Decreed Share & Fraction Parser for Revenue Court Partitions.

Parses decreed fractions (e.g. '1/2', '1/4', '3/8', '1/4 + 1/4', '33.33%', '0.25'),
validates that sum(shares) == 1.0, and never infers shares from genealogy.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Dict, List, Tuple, Union


class ShareValidationError(ValueError):
    pass


def parse_fraction(expr: Union[str, float, int, Fraction]) -> Fraction:
    """Parse a single share expression into an exact Fraction.
    
    Supported formats:
      - Fraction strings: '1/2', '3/8', '5/16'
      - Additive fractions: '1/4 + 1/4', '1/3 + 1/6'
      - Percentages: '50%', '33.33%'
      - Decimals / Floats: '0.25', 0.5
      - Integers: 1 (representing 100%)
    """
    if isinstance(expr, Fraction):
        return expr
    if isinstance(expr, (int, float)):
        # Convert float to fraction with reasonable limit denominator
        return Fraction(expr).limit_denominator(100000)

    s = str(expr).strip()
    if not s:
        raise ShareValidationError("Share expression cannot be empty.")

    # 1. Percentage: e.g. "50%" or "33.33%"
    if s.endswith("%"):
        num_str = s[:-1].strip()
        try:
            val = float(num_str) / 100.0
            return Fraction(val).limit_denominator(100000)
        except ValueError as e:
            raise ShareValidationError(f"Invalid percentage share '{expr}': {e}") from e

    # 2. Additive fractions: e.g. "1/4 + 1/4" or "1/8 + 3/8"
    if "+" in s:
        parts = [p.strip() for p in s.split("+") if p.strip()]
        total = Fraction(0, 1)
        for part in parts:
            total += parse_fraction(part)
        return total

    # 3. Fraction string: e.g. "1/2" or "3/8"
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
            num = int(parts[0].strip())
            den = int(parts[1].strip())
            if den == 0:
                raise ShareValidationError(f"Division by zero in share '{expr}'.")
            return Fraction(num, den)

    # 4. Standard decimal float string: e.g. "0.25"
    try:
        val = float(s)
        return Fraction(val).limit_denominator(100000)
    except ValueError as e:
        raise ShareValidationError(f"Cannot parse share expression '{expr}': {e}") from e


def validate_shares(
    party_shares: Dict[str, Union[str, float, int, Fraction]],
    tol: float = 1e-5
) -> Tuple[bool, Dict[str, float], Dict[str, str], str]:
    """Validate that sum of co-sharer shares equals 1.0 (100%).
    
    Returns:
      (is_valid, float_shares_dict, exact_fraction_strings_dict, explanation_message)
    """
    if not party_shares:
        return False, {}, {}, "No co-sharers or shares provided."

    frac_dict: Dict[str, Fraction] = {}
    float_dict: Dict[str, float] = {}
    str_dict: Dict[str, str] = {}

    for pid, raw_share in party_shares.items():
        try:
            f = parse_fraction(raw_share)
            frac_dict[pid] = f
            float_dict[pid] = float(f)
            str_dict[pid] = str(f)
        except ShareValidationError as e:
            return False, {}, {}, str(e)

    total_frac = sum(frac_dict.values(), Fraction(0, 1))
    total_float = float(total_frac)

    diff = total_float - 1.0

    if abs(diff) <= tol or total_frac == Fraction(1, 1):
        return True, float_dict, str_dict, "Shares sum exactly to 1.0 (100%)."

    if diff < 0:
        pct_under = abs(diff) * 100
        msg = f"अंशों का योग 1 से कम है (Total: {total_float:.4f}, Under-allocated by {pct_under:.2f}%)."
    else:
        pct_over = diff * 100
        msg = f"अंशों का योग 1 से अधिक है (Total: {total_float:.4f}, Over-allocated by {pct_over:.2f}%)."

    return False, float_dict, str_dict, msg
