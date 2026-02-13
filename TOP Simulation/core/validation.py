"""
TOP v3.1 - Canonical Validation with Burn Reservation
"""

from typing import List, Dict, Any, Set
from .events import sort_events

def canonical_burn_split(burn: int, signers: List[str]) -> Dict[str, int]:
    """
    Canonical H7 burn split.
    
    Args:
        burn: Total burn amount
        signers: Sorted list of signer IDs
    
    Returns:
        Dict mapping signer_id -> burn_amount
        
    Rule:
        q = floor(burn / n)
        r = burn - n*q
        First signer (lexicographic) gets q+r, rest get q
    """
    n = len(signers)
    if n == 0:
        raise ValueError("Cannot split burn with 0 signers")
    
    q = burn // n
    r = burn - n * q
    
    burn_split = {}
    for i, signer in enumerate(signers):
        if i == 0:
            burn_split[signer] = q + r
        else:
            burn_split[signer] = q
    
    return burn_split

def validate_events(
    candidates: List[Dict[str, Any]],
    state_prev: Dict[str, Any],
    log: Set[str],
    theta: Dict[str, Any],
    T: int
) -> List[Dict[str, Any]]:
    """
    Canonical validation procedure (Steps V1-V5).
    
    Args:
        candidates: List of candidate events for epoch T
        state_prev: Previous state (epoch T-1)
        log: Set of all accepted event IDs in L (up to T-1)
        theta: Theta parameters
        T: Current epoch
    
    Returns:
        List of validated events
    """
    # Sort candidates lexicographically by ID
    candidates = sort_events(candidates)
    
    # Initialize burn reservation map
    R_burn = {}
    for agent in state_prev.get('agents', {}):
        R_burn[agent] = 0
    
    validated = []
    
    for event in candidates:
        event_id = event['id']
        event_type = event['type']
        signers = sorted(event['signers'])
        parents = event.get('parents', [])
        burn = event.get('burn', 0)
        
        # Step V1: Structural + Type Checks
        try:
            # Empty signers
            if len(signers) == 0:
                continue  # Reject
            
            # Max signers
            if len(signers) > theta['N_sig_max']:
                continue  # Reject
            
            # Max parents
            if len(parents) > theta['K_parents']:
                continue  # Reject
            
            # Type-specific checks
            if event_type in ['STANDARD', 'DEMAND', 'CONFIRM']:
                if burn <= 0:
                    continue  # Reject
            
            if event_type == 'INVESTMINT':
                if burn != 0:
                    continue  # Reject
                if event.get('delta_s', 0) <= 0:
                    continue  # Reject
                if len(signers) != 1:
                    continue  # Reject
            
            if event_type == 'COLLATERAL_DEPOSIT':
                if burn != 0:
                    continue  # Reject
                if event.get('deposit', 0) <= 0:
                    continue  # Reject
                if len(signers) != 1:
                    continue  # Reject
            
            if event_type in ['DEMAND', 'CONFIRM']:
                if 'sku' not in event:
                    continue  # Reject
                if event['sku'] not in theta['SKUs']:
                    continue  # Reject
                if event.get('quantity', 0) <= 0:
                    continue  # Reject
        
        except Exception:
            continue  # Reject on any error
        
        # Step V2: Parent Validity
        valid_parents = True
        for parent_id in parents:
            if parent_id not in log:
                valid_parents = False
                break
            # Future parent check would require epoch lookup
            # For now assume parents are valid (caller ensures)
        
        if not valid_parents:
            continue  # Reject
        
        # Step V3: Canonical Burn Split
        burn_split = canonical_burn_split(burn, signers)
        
        # Step V4: Pre-Check Reservation (No Rollback)
        can_afford = True
        for signer in signers:
            # Get agent balance (default to 0 if new agent)
            E_prev = state_prev['agents'].get(signer, {}).get('E', 0)
            reserved = R_burn.get(signer, 0)
            
            if E_prev - reserved < burn_split[signer]:
                can_afford = False
                break
        
        if not can_afford:
            continue  # Reject permanently
        
        # Step V5: Reservation Update
        for signer in signers:
            if signer not in R_burn:
                R_burn[signer] = 0
            R_burn[signer] += burn_split[signer]
        
        # Accept event
        event['burn_split'] = burn_split  # Store for later use
        validated.append(event)
    
    return validated