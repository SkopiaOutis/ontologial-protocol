"""
TOP v3.1 - Stasis Mechanism
Rest, Accumulation, Realization, Auto-Liquidation
"""

from typing import Dict, Any, List
from .primitives import mul_fp, div_fp, check_i128, clip, floor_div
from .dac import DAC

def update_rest_counters(
    validated: List[Dict[str, Any]],
    agents: Dict[str, Any]
) -> Dict[str, int]:
    """
    Update rest counters.
    
    Production events (STANDARD, CONFIRM) reset rest to 0.
    All others increment rest.
    """
    rest = {}
    
    # Get producers
    producers = set()
    for event in validated:
        if event['type'] in ['STANDARD', 'CONFIRM']:
            for signer in event['signers']:
                producers.add(signer)
    
    # Update rest
    for agent_id, agent_data in agents.items():
        if agent_id in producers:
            rest[agent_id] = 0
        else:
            rest[agent_id] = agent_data.get('rest', 0) + 1
    
    return rest

def accumulate_native_stasis(
    rest: Dict[str, int],
    agents: Dict[str, Any],
    rho_fp: int,
    dac: DAC,
    FPONE: int
) -> Dict[str, int]:
    """
    Accumulate native stasis: S^native += rho * log(1 + rest)
    """
    S_native = {}
    
    for agent_id, agent_data in agents.items():
        S_prev = agent_data.get('S_native', 0)
        r = rest.get(agent_id, 0)
        
        # log(1 + rest)
        log_input = (1 + r) * FPONE
        log_val = dac.log_fp(log_input)
        
        # Increment
        increment = mul_fp(rho_fp, log_val, FPONE)
        S_native[agent_id] = S_prev + increment
        check_i128(S_native[agent_id], f"S_native[{agent_id}]")
    
    return S_native

def compute_stasis_realization(
    S_native: Dict[str, int],
    DCD_fp: Dict[str, int],
    X_fp: Dict[str, int],
    M_T: int,
    M_target: int,
    eta_S_0_fp: int,
    FPONE: int
) -> Dict[str, Any]:
    """
    Compute max realizable stasis per agent.
    
    Returns:
        Dict with S_real_max, S_native_updated, eta_eff
    """
    # Average planetary stress
    if X_fp:
        X_avg_fp = sum(X_fp.values()) // len(X_fp)
    else:
        X_avg_fp = 0
    
    # Activity factor
    activity_fp = div_fp(M_T * FPONE, M_target, FPONE)
    
    # Stress factor
    stress_fp = FPONE + X_avg_fp
    
    # Effective realization factor
    eta_eff_fp = mul_fp(
        eta_S_0_fp,
        div_fp(activity_fp, stress_fp, FPONE),
        FPONE
    )
    
    # Total structural mass
    Sigma_DCD = sum(DCD_fp.values())
    check_i128(Sigma_DCD, "Sigma_DCD")
    
    # Max realizable per agent
    S_real_max = {}
    S_native_updated = {}
    
    for agent_id, s_native in S_native.items():
        # Cap by native and by system activity
        cap_by_system = mul_fp(eta_eff_fp, Sigma_DCD, FPONE)
        s_real = min(s_native, cap_by_system)
        
        S_real_max[agent_id] = s_real
        
        # Deduct from native
        S_native_updated[agent_id] = s_native - s_real
        check_i128(S_native_updated[agent_id], f"S_native_updated[{agent_id}]")
    
    return {
        'S_real_max': S_real_max,
        'S_native': S_native_updated,
        'eta_eff_fp': eta_eff_fp
    }

def auto_liquidation(
    validated: List[Dict[str, Any]],
    S_real_max: Dict[str, int],
    CapRem_sys: int,
    Cap_ind: int,
    agents: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Auto-liquidation on production events.
    
    Scans events in lexicographic order.
    """
    S_real_rem = {a: s for a, s in S_real_max.items()}
    Delta_auto_total = 0
    
    # Sort events by ID (lexicographic)
    events_sorted = sorted(validated, key=lambda e: e['id'])
    
    for event in events_sorted:
        if event['type'] not in ['STANDARD', 'CONFIRM']:
            continue
        
        # Sort signers lexicographically
        signers = sorted(event['signers'])
        
        for signer in signers:
            # Compute auto amount
            s_rem = S_real_rem.get(signer, 0)
            delta = min(s_rem, Cap_ind, CapRem_sys)
            
            if delta > 0:
                # Apply
                agents[signer]['E'] += delta
                check_i128(agents[signer]['E'], f"E[{signer}] after auto-liq")
                
                S_real_rem[signer] -= delta
                CapRem_sys -= delta
                Delta_auto_total += delta
    
    # Forfeit remaining
    # (just don't carry forward)
    
    return {
        'Delta_auto_total': Delta_auto_total,
        'CapRem_sys': CapRem_sys
    }