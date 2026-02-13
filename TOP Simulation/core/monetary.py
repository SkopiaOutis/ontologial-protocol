"""
TOP v3.1 - Monetary Layer
Burn Budget, Mint Budget, Income Allocation
"""

from typing import List, Dict, Any
from .primitives import mul_fp, div_fp, check_i128, floor_div

def compute_burn_budget(validated: List[Dict[str, Any]]) -> int:
    """Compute epoch burn budget B_T (sum of burns)."""
    B_T = 0
    for event in validated:
        B_T += event.get('burn', 0)
    return check_i128(B_T, "B_T")

def compute_mint_budget(B_T: int, epsilon_fp: int, FPONE: int) -> int:
    """Compute epoch mint budget M_T = B_T + elastic_expansion."""
    elastic_term = (epsilon_fp * B_T) // FPONE
    M_T = B_T + elastic_term
    return check_i128(M_T, "M_T")

def compute_event_potential(
    event: Dict[str, Any],
    DCD_fp: Dict[str, int],
    lambda_b_fp: int,
    FPONE: int
) -> int:
    """
    Compute event potential P_fp_T(e).
    CRITICAL: This balances Structure (DCD) vs Energy (Burn).
    Sybil Resistance depends on lambda_b_fp being LOW.
    """
    event_id = event['id']
    
    # DCD component (Structure)
    dcd = DCD_fp.get(event_id, 0)
    
    # Burn component (Energy)
    burn_base = event.get('burn', 0)
    burn_fp = burn_base * FPONE
    
    # Weighting: If lambda_b is 1.0, Burn dominates. If 0.1, Structure dominates.
    burn_weighted = mul_fp(lambda_b_fp, burn_fp, FPONE)
    
    # Total potential
    P_fp = dcd + burn_weighted
    
    return check_i128(P_fp, f"P_fp[{event_id}]")

def allocate_income(
    validated: List[Dict[str, Any]],
    DCD_fp: Dict[str, int],
    M_T: int,
    lambda_b_fp: int,
    epsilon_num_fp: int,
    FPONE: int
) -> Dict[str, Dict[str, int]]:
    """Canonical income allocation using floor division."""
    
    # 1. Compute Potentials
    P_fp = {}
    Sigma_fp = 0
    
    for event in validated:
        p = compute_event_potential(event, DCD_fp, lambda_b_fp, FPONE)
        P_fp[event['id']] = p
        Sigma_fp += p
    
    check_i128(Sigma_fp, "Sigma_fp")
    
    # 2. Denominator (Sum + Stabilizer)
    Den_fp = Sigma_fp + epsilon_num_fp
    
    # 3. Allocate Income to Events
    event_income = {}
    for event in validated:
        event_id = event['id']
        p = P_fp[event_id]
        
        # Formula: I = floor( (M_T * P) / Den )
        N = M_T * p
        check_i128(N, f"income_numerator[{event_id}]")
        
        I = N // Den_fp
        event_income[event_id] = I
    
    # 4. Split Income to Signers (H8 Rule)
    agent_income = {}
    for event in validated:
        event_id = event['id']
        I = event_income[event_id]
        signers = sorted(event['signers'])
        n = len(signers)
        
        if n == 0: continue
        
        q = I // n
        r = I - n * q
        
        for i, signer in enumerate(signers):
            if signer not in agent_income:
                agent_income[signer] = 0
            
            # First signer gets remainder
            agent_income[signer] += (q + r) if i == 0 else q
    
    return {
        'event_income': event_income,
        'agent_income': agent_income
    }