"""
TOP v3.1 - Fixed-Point Primitives
All arithmetic is i128 with deterministic overflow abort.
"""

import sys

# i128 bounds
I128_MIN = -(2**127)
I128_MAX = 2**127 - 1

def check_i128(x: int, context: str = "") -> int:
    """Abort if x overflows i128."""
    if not (I128_MIN <= x <= I128_MAX):
        raise OverflowError(f"i128 overflow in {context}: {x}")
    return x

def mul_fp(a_fp: int, b_fp: int, FPONE: int) -> int:
    """
    Fixed-point multiplication: floor((a * b) / FPONE)
    
    Args:
        a_fp, b_fp: Fixed-point integers
        FPONE: Fixed-point unit (10^k)
    
    Returns:
        floor((a_fp * b_fp) / FPONE)
    
    Raises:
        OverflowError if intermediate product exceeds i128
    """
    product = a_fp * b_fp
    check_i128(product, f"mul_fp({a_fp}, {b_fp})")
    return product // FPONE

def div_fp(a_fp: int, b_fp: int, FPONE: int) -> int:
    """
    Fixed-point division: floor((a * FPONE) / b)
    
    Args:
        a_fp: Numerator (fixed-point)
        b_fp: Denominator (fixed-point), must be > 0
        FPONE: Fixed-point unit
    
    Returns:
        floor((a_fp * FPONE) / b_fp)
    
    Raises:
        ValueError if b_fp <= 0
        OverflowError if intermediate product exceeds i128
    """
    if b_fp <= 0:
        raise ValueError(f"div_fp: denominator must be positive, got {b_fp}")
    
    numerator = a_fp * FPONE
    check_i128(numerator, f"div_fp({a_fp}, {b_fp})")
    return numerator // b_fp

def clip(x: int, x_min: int, x_max: int) -> int:
    """
    Deterministic clipping.
    
    Returns:
        x_min if x < x_min
        x_max if x > x_max
        x otherwise
    """
    if x < x_min:
        return x_min
    if x > x_max:
        return x_max
    return x

def floor_div(a: int, b: int) -> int:
    """
    Integer floor division.
    Python's // operator for integers.
    
    Args:
        a: Dividend
        b: Divisor (must be > 0)
    
    Returns:
        floor(a / b)
    """
    if b <= 0:
        raise ValueError(f"floor_div: divisor must be positive, got {b}")
    return a // b