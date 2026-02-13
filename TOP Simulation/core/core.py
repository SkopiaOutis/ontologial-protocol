"""
TOP v3.1 - Fixed-Point Core Dynamics
Ripple, DCD, Attribution
"""

from typing import List, Dict, Any
from .primitives import mul_fp, div_fp, check_i128, clip
from .dac import DAC

def compute_temporal_decay(
    parent_epoch: int,
    child_epoch: int,
    tau: int,
    dac: DAC,
    FPONE: int
) -> int:
    """
    Canonical temporal decay.
    
    Args:
        parent_epoch: Epoch of parent event
        child_epoch: Epoch of child event
        tau: Decay time constant
        dac: DAC instance for exp_fp
        FPONE: Fixed-point unit
    
    Returns:
        lambda_{T,fp}(parent, child) in fixed-point
    """
    delta = child_epoch - parent_epoch
    if delta < 1:
        raise ValueError(f"Invalid parent-child epoch: {parent_epoch} -> {child_epoch}")
    
    # u = -floor(delta * FPONE / tau)
    u_raw = -(delta * FPONE // tau)
    
    # Promote to fixed-point and clip
    u_fp = u_raw * FPONE
    u_fp = clip(u_fp, dac.u_min_fp, dac.u_max_fp)
    
    # Decay factor
    lambda_fp = dac.exp_fp(u_fp)
    
    return lambda_fp

def compute_ripple(
    horizon: List[Dict[str, Any]],
    ripple_order: List[Dict[str, Any]],
    alpha_stored_prev: Dict[str, int],
    gamma_fp: int,
    tau: int,
    dac: DAC,
    FPONE: int
) -> Dict[str, int]:
    """
    Compute Ripple for all events in horizon.
    
    Args:
        horizon: List of all horizon events
        ripple_order: Events in RippleOrder (children before parents)
        alpha_stored_prev: Attribution from T-1 (stored convention)
        gamma_fp: Ripple damping factor
        tau: Decay time constant
        dac: DAC instance
        FPONE: Fixed-point unit
    
    Returns:
        Dict mapping event_id -> R_fp_T
    """
    # Promote burn to fixed-point
    b_fp = {}
    for e in horizon:
        b_fp[e['id']] = e.get('burn', 0) * FPONE
    
    # Build children map
    children_map = {e['id']: [] for e in horizon}
    event_map = {e['id']: e for e in horizon}
    
    for event in horizon:
        for parent_id in event.get('parents', []):
            if parent_id in children_map:
                children_map[parent_id].append(event['id'])
    
    # Sort children lexicographically
    for parent_id in children_map:
        children_map[parent_id].sort()
    
    # Compute Ripple
    R_fp = {}
    
    for event in ripple_order:
        event_id = event['id']
        
        # Base: burn
        ripple = b_fp[event_id]
        
        # Add contributions from children
        for child_id in children_map[event_id]:
            child = event_map[child_id]
            
            # Temporal decay
            lambda_fp = compute_temporal_decay(
                event['epoch'],
                child['epoch'],
                tau,
                dac,
                FPONE
            )
            
            # Attribution
            alpha_fp = alpha_stored_prev.get(child_id, 0)
            
            # Number of parents
            n_parents = len(child.get('parents', []))
            if n_parents == 0:
                n_parents = 1  # Avoid division by zero
            
            # C_fp = lambda * floor(R * alpha / n_parents)
            R_child = R_fp.get(child_id, 0)
            weighted = mul_fp(R_child, alpha_fp, FPONE)
            per_parent = weighted // n_parents
            decayed = mul_fp(lambda_fp, per_parent, FPONE)
            contribution = mul_fp(gamma_fp, decayed, FPONE)
            
            ripple += contribution
        
        R_fp[event_id] = check_i128(ripple, f"R_fp[{event_id}]")
    
    return R_fp

def compute_dcd(
    horizon: List[Dict[str, Any]],
    R_fp: Dict[str, int],
    dac: DAC,
    FPONE: int
) -> Dict[str, int]:
    """
    Compute DCD (Distributed Contribution Density).
    
    Args:
        horizon: List of horizon events
        R_fp: Ripple values
        dac: DAC instance
        FPONE: Fixed-point unit
    
    Returns:
        Dict mapping event_id -> DCD_fp_T
    """
    # Build children map
    children_map = {e['id']: set() for e in horizon}
    
    for event in horizon:
        for parent_id in event.get('parents', []):
            if parent_id in children_map:
                children_map[parent_id].add(event['id'])
    
    DCD_fp = {}
    
    for event in horizon:
        event_id = event['id']
        n_children = len(children_map[event_id])
        
        # Structural intensity: log(1 + n_children)
        input_val = (1 + n_children) * FPONE
        sigma_fp = dac.log_fp(input_val)
        
        # DCD = sigma * R
        dcd = mul_fp(sigma_fp, R_fp[event_id], FPONE)
        
        print(f"  DCD = {dcd}")
        
        DCD_fp[event_id] = check_i128(dcd, f"DCD_fp[{event_id}]")
    
    return DCD_fp

def compute_attribution(
    horizon: List[Dict[str, Any]],
    DCD_fp: Dict[str, int],
    epsilon_num_fp: int,
    FPONE: int
) -> Dict[str, int]:
    """
    Compute Attribution for next epoch.
    
    Args:
        horizon: List of horizon events
        DCD_fp: DCD values
        epsilon_num_fp: Numerical stabilizer
        FPONE: Fixed-point unit
    
    Returns:
        Dict mapping event_id -> alpha_stored_T (for use in T+1)
    """
    # Total structural mass
    Z_fp = sum(DCD_fp.values())
    check_i128(Z_fp, "Z_fp")
    
    # Denominator
    Den_fp = Z_fp + epsilon_num_fp
    
    print(f"Den_fp = {Den_fp}")
    print("=" * 30)
    
    # Attribution
    alpha_stored = {}
    for event_id, dcd in DCD_fp.items():
        alpha = div_fp(dcd, Den_fp, FPONE)
        alpha_stored[event_id] = alpha
    
    return alpha_stored



