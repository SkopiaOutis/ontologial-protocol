"""
TOP v3.1 - Economic Module
Backlog, Scarcity, Pressure, Planetary Stress, Workforce
"""

from typing import Dict, Any, List
from .primitives import mul_fp, div_fp, check_i128, clip, floor_div
from .dac import DAC

def update_backlog_supply(
    validated: List[Dict[str, Any]],
    state_prev: Dict[str, Any],
    theta: Dict[str, Any],
    FPONE: int
) -> Dict[str, Any]:
    """
    Update backlog and smoothed supply.
    
    Returns:
        Dict with B_T, S_bar_T for all SKUs
    """
    # Extract parameters
    delta_B_fp = theta['delta_B_fp']
    xi_fp = theta['xi_fp']
    SKUs = theta.get('SKUs', [])
    
    if not SKUs:
        return {'B_T': {}, 'S_bar_T': {}}
    
    # Compute demand and supply this epoch
    D_T = {sku: 0 for sku in SKUs}
    S_T = {sku: 0 for sku in SKUs}
    
    for event in validated:
        if event['type'] == 'DEMAND':
            sku = event['sku']
            if sku in D_T:
                D_T[sku] += event['quantity']
        elif event['type'] == 'CONFIRM':
            sku = event['sku']
            if sku in S_T:
                S_T[sku] += event['quantity']
    
    # Previous state
    B_prev = state_prev.get('B_T', {sku: 0 for sku in SKUs})
    S_bar_prev = state_prev.get('S_bar_T', {sku: FPONE for sku in SKUs})  # Start at 1
    
    # Update backlog
    B_T = {}
    for sku in SKUs:
        decay = (FPONE - delta_B_fp) * B_prev.get(sku, 0) // FPONE
        net = D_T[sku] - S_T[sku]
        B_T[sku] = max(0, decay + net)
        check_i128(B_T[sku], f"B_T[{sku}]")
    
    # Update smoothed supply
    S_bar_T = {}
    for sku in SKUs:
        old_term = (FPONE - xi_fp) * S_bar_prev.get(sku, FPONE)
        new_term = xi_fp * S_T[sku]
        S_bar_T[sku] = (old_term + new_term) // FPONE
        check_i128(S_bar_T[sku], f"S_bar_T[{sku}]")
    
    return {'B_T': B_T, 'S_bar_T': S_bar_T, 'D_T': D_T, 'S_T': S_T}

def compute_scarcity_pressure(
    B_T: Dict[str, int],
    S_bar_T: Dict[str, int],
    S_T: Dict[str, int],
    L_fp: Dict[str, int],
    A_fp: Dict[str, int],
    lambda_u_fp: int,
    epsilon_num_fp: int,
    FPONE: int
) -> Dict[str, Any]:
    """Compute scarcity, capacity, utilization, pressure."""
    
    SKUs = list(B_T.keys())
    
    # Scarcity
    chi_fp = {}
    for sku in SKUs:
        num = B_T[sku] * FPONE
        den = S_bar_T[sku] * FPONE + epsilon_num_fp
        chi_fp[sku] = div_fp(num, den, FPONE)
    
    # Capacity
    O_fp = {}
    for sku in SKUs:
        O_fp[sku] = mul_fp(A_fp.get(sku, FPONE), L_fp.get(sku, 0), FPONE)
    
    # Utilization
    u_fp = {}
    for sku in SKUs:
        num = S_T[sku] * FPONE
        den = O_fp[sku] + epsilon_num_fp
        u_fp[sku] = div_fp(num, den, FPONE)
    
    # Pressure
    Phi_fp = {}
    for sku in SKUs:
        underutil = FPONE - u_fp[sku]
        penalty = mul_fp(lambda_u_fp, underutil, FPONE)
        Phi_fp[sku] = chi_fp[sku] - penalty
    
    return {
        'chi_fp': chi_fp,
        'O_fp': O_fp,
        'u_fp': u_fp,
        'Phi_fp': Phi_fp
    }

def update_planetary_stress(
    S_T: Dict[str, int],
    state_prev: Dict[str, Any],
    theta: Dict[str, Any],
    FPONE: int
) -> Dict[str, int]:
    """Update planetary stress X_fp."""
    
    zeta_fp = theta['zeta_fp']
    Planets = theta.get('Planets', [])
    imp_fp = theta.get('imp_fp', {})
    
    if not Planets:
        return {}
    
    X_prev = state_prev.get('X_fp', {p: 0 for p in Planets})
    X_fp = {}
    
    for planet in Planets:
        # Compute impact term
        term = 0
        for sku, s in S_T.items():
            impact = imp_fp.get(sku, {}).get(planet, 0)
            term += mul_fp(s * FPONE, impact, FPONE)
        
        # EMA update
        old_part = mul_fp(FPONE - zeta_fp, X_prev.get(planet, 0), FPONE)
        new_part = mul_fp(zeta_fp, term, FPONE)
        X_fp[planet] = old_part + new_part
        check_i128(X_fp[planet], f"X_fp[{planet}]")
    
    return X_fp

def compute_planetary_multiplier(
    X_fp: Dict[str, int],
    theta: Dict[str, Any],
    FPONE: int
) -> Dict[str, int]:
    """Compute planetary multiplier mu_fp."""
    
    kappa_X_fp = theta['kappa_X_fp']
    mu_max_fp = theta['mu_max_fp']
    imp_fp = theta.get('imp_fp', {})
    SKUs = theta.get('SKUs', [])
    
    mu_fp = {}
    
    for sku in SKUs:
        stress_contrib = 0
        for planet, x in X_fp.items():
            impact = imp_fp.get(sku, {}).get(planet, 0)
            stress_contrib += mul_fp(x, impact, FPONE)
        
        mu_raw = FPONE + mul_fp(kappa_X_fp, stress_contrib, FPONE)
        mu_fp[sku] = clip(mu_raw, FPONE, mu_max_fp)
    
    return mu_fp

def update_log_prices(
    Phi_fp: Dict[str, int],
    mu_fp: Dict[str, int],
    state_prev: Dict[str, Any],
    theta: Dict[str, Any],
    dac: DAC,
    FPONE: int
) -> Dict[str, Any]:
    """Update log-prices and prices."""
    
    kappa_p_fp = theta['kappa_p_fp']
    l_min_fp = theta['l_min_fp']
    l_max_fp = theta['l_max_fp']
    SKUs = theta.get('SKUs', [])
    
    l_prev = state_prev.get('l_fp', {sku: 0 for sku in SKUs})
    Phi_prev = state_prev.get('Phi_fp', {sku: 0 for sku in SKUs})
    mu_prev = state_prev.get('mu_fp', {sku: FPONE for sku in SKUs})
    
    l_fp = {}
    p_fp = {}
    
    for sku in SKUs:
        # Pressure adjustment
        pressure_adj = mul_fp(kappa_p_fp, Phi_prev.get(sku, 0), FPONE)
        
        # Planetary adjustment
        log_mu = dac.log_fp(mu_prev.get(sku, FPONE))
        
        # Update
        l_raw = l_prev.get(sku, 0) + pressure_adj + log_mu
        l_fp[sku] = clip(l_raw, l_min_fp, l_max_fp)
        
        # Price
        p_fp[sku] = dac.exp_fp(l_fp[sku])
    
    return {'l_fp': l_fp, 'p_fp': p_fp}

def update_workforce(
    chi_fp: Dict[str, int],
    l_fp: Dict[str, int],
    state_prev: Dict[str, Any],
    theta: Dict[str, Any],
    dac: DAC,
    FPONE: int
) -> Dict[str, int]:
    """Update workforce allocation via softmax."""
    
    alpha_chi_fp = theta['alpha_chi_fp']
    nu_fp = theta['nu_fp']
    epsilon_num_fp = theta['epsilon_num_fp']
    SKUs = theta.get('SKUs', [])
    
    if not SKUs:
        return {}
    
    pi_prev = state_prev.get('pi_fp', {sku: FPONE // len(SKUs) for sku in SKUs})
    
    # Compute utility
    a_fp = {}
    for sku in SKUs:
        price_part = l_fp.get(sku, 0)
        scarcity_part = mul_fp(alpha_chi_fp, chi_fp.get(sku, 0), FPONE)
        a_fp[sku] = price_part + scarcity_part
    
    # Max-stabilized softmax
    m = max(a_fp.values()) if a_fp else 0
    
    N_fp = {}
    for sku in SKUs:
        N_fp[sku] = dac.exp_fp(a_fp[sku] - m)
    
    Pi_fp = sum(N_fp.values()) + epsilon_num_fp
    
    pi_fp = {}
    for sku in SKUs:
        pi_fp[sku] = div_fp(N_fp[sku], Pi_fp, FPONE)
    
    # Update workforce
    L_fp = {}
    for sku in SKUs:
        old_part = mul_fp(FPONE - nu_fp, state_prev.get('L_fp', {}).get(sku, FPONE // len(SKUs)), FPONE)
        new_part = mul_fp(nu_fp, pi_prev.get(sku, FPONE // len(SKUs)), FPONE)
        L_fp[sku] = old_part + new_part
    
    # Normalization
    total = sum(L_fp.values())
    remainder = FPONE - total
    
    if remainder != 0 and SKUs:
        first_sku = min(SKUs)  # Lexicographically smallest
        L_fp[first_sku] += remainder
    
    return {'L_fp': L_fp, 'pi_fp': pi_fp}