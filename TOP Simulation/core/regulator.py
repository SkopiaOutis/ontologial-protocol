"""
TOP v3.1 - Regulator Layer
Branching degree, smoothed branching, elasticity
"""

from typing import Dict, Any, List
from .primitives import mul_fp, check_i128, clip

def compute_branching_degree(
    horizon: List[Dict[str, Any]],
    FPONE: int
) -> int:
    """
    Compute branching degree sigma_fp.
    """
    n = len(horizon)
    
    if n == 0:
        return 0
    
    # Count total children
    C = 0
    for event in horizon:
        C += len(event.get('parents', []))  # Each event counts parents = contributes to parent's children
    
    # Average
    sigma_fp = (C * FPONE) // n
    
    return check_i128(sigma_fp, "sigma_fp")

def update_smoothed_branching(
    sigma_fp: int,
    sigma_hat_prev: int,
    beta_fp: int,
    FPONE: int
) -> int:
    """
    Update smoothed branching: EMA with beta.
    """
    diff = sigma_fp - sigma_hat_prev
    step = mul_fp(beta_fp, diff, FPONE)
    sigma_hat = sigma_hat_prev + step
    
    return check_i128(sigma_hat, "sigma_hat_fp")

def update_elasticity(
    sigma_hat_fp: int,
    epsilon_prev: int,
    sigma_target_fp: int,
    kappa_P_fp: int,
    epsilon_min_fp: int,
    epsilon_max_fp: int,
    FPONE: int
) -> int:
    """
    Update elasticity: PID control toward target branching.
    """
    # Deviation
    Delta_fp = sigma_target_fp - sigma_hat_fp
    
    # Regulator step
    step_fp = mul_fp(kappa_P_fp, Delta_fp, FPONE)
    
    # Update
    epsilon_raw = epsilon_prev + step_fp
    
    # Clip
    epsilon_fp = clip(epsilon_raw, epsilon_min_fp, epsilon_max_fp)
    
    return check_i128(epsilon_fp, "epsilon_fp")