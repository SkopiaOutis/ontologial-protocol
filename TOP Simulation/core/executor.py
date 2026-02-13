"""
TOP v3.1 - Canonical Epoch Executor
"""

from .stasis import (
    update_rest_counters,
    accumulate_native_stasis,
    compute_stasis_realization,
    auto_liquidation
)
from .regulator import (
    compute_branching_degree,
    update_smoothed_branching,
    update_elasticity
)

from typing import Dict, Any, List, Set
from .validation import validate_events
from .horizon import construct_horizon, canonical_kahn
from .core import compute_ripple, compute_dcd, compute_attribution
from .monetary import compute_burn_budget, compute_mint_budget, allocate_income
from .economic import (
    update_backlog_supply,
    compute_scarcity_pressure,
    update_planetary_stress,
    compute_planetary_multiplier,
    update_log_prices,
    update_workforce
)
from .serialization import compute_state_hash, compute_theta_hash
from .dac import DAC
from .primitives import check_i128

def execute_epoch(
    theta: Dict[str, Any],
    state_prev: Dict[str, Any],
    log_prev: List[Dict[str, Any]],
    candidates: List[Dict[str, Any]],
    T: int
) -> Dict[str, Any]:
    """Execute canonical epoch pipeline."""
    
    FPONE = theta['FPONE']
    
    # Initialize DAC (only once per execution)
    if 'dac' not in state_prev:
        dac = DAC(theta)
    else:
        dac = state_prev['dac']
    
    # Build log ID set for validation
    log_ids = {e['id'] for e in log_prev}
    
    # Step 1: Validation
    validated = validate_events(
        candidates,
        state_prev,
        log_ids,
        theta,
        T
    )
    
    print(f"Epoch {T}: {len(validated)}/{len(candidates)} events validated")
    
    # Step 2: Apply Burn
    agents = {}
    for agent_id, agent_data in state_prev.get('agents', {}).items():
        agents[agent_id] = agent_data.copy()
    
    for event in validated:
        for signer, burn_amount in event['burn_split'].items():
            if signer not in agents:
                agents[signer] = {
                    'E': 0,
                    'S_native': 0,
                    'S_coll': 0,
                    'rest': 0
                }
            
            agents[signer]['E'] -= burn_amount
            agents[signer]['E'] = check_i128(agents[signer]['E'], f"E[{signer}] after burn")
    
    # Update log
    log_current = log_prev + validated

    # Step 2: Apply Burn
    agents = {}
    for agent_id, agent_data in state_prev.get('agents', {}).items():
        agents[agent_id] = agent_data.copy()
    
    for event in validated:
        for signer, burn_amount in event['burn_split'].items():
            if signer not in agents:
                agents[signer] = {
                    'E': 0,
                    'S_native': 0,
                    'S_coll': 0,
                    'rest': 0
                }
            
            agents[signer]['E'] -= burn_amount
            agents[signer]['E'] = check_i128(agents[signer]['E'], f"E[{signer}] after burn")
    
    # Initialize M_liq after burn (before any increments)
    M_liq = sum(agent['E'] for agent in agents.values())
    
    # Update log
    log_current = log_prev + validated
    
    # Step 3: Horizon Construction
    horizon = construct_horizon(log_current, T, theta['H'])
    
    # Step 4: DAG Traversal
    ripple_order = canonical_kahn(horizon)
    
    # Step 5: Structural Core
    alpha_stored_prev = {}
    for hid, he in state_prev.get('horizon_events', {}).items():
        alpha_stored_prev[hid] = he.get('alpha_stored', 0)
    
    R_fp = compute_ripple(
        horizon,
        ripple_order,
        alpha_stored_prev,
        theta['gamma_fp'],
        theta['tau'],
        dac,
        FPONE
    )
    
    DCD_fp = compute_dcd(horizon, R_fp, dac, FPONE)
    
    alpha_stored = compute_attribution(
        horizon,
        DCD_fp,
        theta['epsilon_num_fp'],
        FPONE
    )
    
    # Step 6: Mint Budget
    B_T = compute_burn_budget(validated)
    
    epsilon_fp = state_prev.get('epsilon_fp', theta.get('epsilon_init_fp', FPONE))
    
    M_T = compute_mint_budget(B_T, epsilon_fp, FPONE)
    
    # Step 7: InvestMint (simplified - not implemented yet, just reserve cap)
    Cap_sys_T = (theta.get('theta_0_fp', 0) * M_T) // FPONE
    CapRem_sys = Cap_sys_T  # Would be depleted by InvestMint

    M_liq_prev = state_prev.get('M_liq', 0)
    Cap_ind_T = (theta.get('phi_0_fp', 100000000) * M_liq_prev) // FPONE
    
    
    # Step 8: Stasis Updates
    rest = update_rest_counters(validated, agents)
    
    S_native = accumulate_native_stasis(
        rest,
        agents,
        theta.get('rho_fp', 10000000),  # Default 0.1
        dac,
        FPONE
    )
    
    stasis_result = compute_stasis_realization(
    S_native,
    DCD_fp,
    state_prev.get('X_fp', {}),  # ← Verwende vorherigen State!
    M_T,
    theta.get('M_target', 1000),
    theta.get('eta_S_0_fp', 10000000),
    FPONE
)
    
    # Update agents with new S_native (after deduction)
    for agent_id in agents:
        agents[agent_id]['S_native'] = stasis_result['S_native'].get(agent_id, 0)
        agents[agent_id]['rest'] = rest.get(agent_id, 0)
    
    # Step 9: Auto-Liquidation
    auto_liq_result = auto_liquidation(
        validated,
        stasis_result['S_real_max'],
        CapRem_sys,
        Cap_ind_T,
        agents
    )
    
    # Update M_liq with auto-liquidation
    M_liq += auto_liq_result['Delta_auto_total']
    
    # Step 10: Income Allocation
    income_result = allocate_income(
        validated,
        DCD_fp,
        M_T,
        theta['lambda_b_fp'],
        theta['epsilon_num_fp'],
        FPONE
    )
    
    # Apply income
    for agent_id, income in income_result['agent_income'].items():
        if agent_id not in agents:
            agents[agent_id] = {
                'E': 0,
                'S_native': 0,
                'S_coll': 0,
                'rest': 0
            }
        
        agents[agent_id]['E'] += income
        agents[agent_id]['E'] = check_i128(agents[agent_id]['E'], f"E[{agent_id}] after income")
    
    # Recompute M_liq
    M_liq_final = sum(agent['E'] for agent in agents.values())
    M_liq = M_liq_final

    # Step 11: Economic Module (if enabled)
    SKUs = theta.get('SKUs', [])
    economic_state = {}
    
    if SKUs:
        # Backlog + Supply
        backlog_supply = update_backlog_supply(validated, state_prev, theta, FPONE)
        
        # Scarcity + Pressure
        A_fp = theta.get('A_fp', {sku: FPONE for sku in SKUs})
        L_fp = state_prev.get('L_fp', {sku: FPONE // len(SKUs) for sku in SKUs})
        
        scarcity_pressure = compute_scarcity_pressure(
            backlog_supply['B_T'],
            backlog_supply['S_bar_T'],
            backlog_supply['S_T'],
            L_fp,
            A_fp,
            theta['lambda_u_fp'],
            theta['epsilon_num_fp'],
            FPONE
        )
        
        # Planetary Stress
        X_fp = update_planetary_stress(
            backlog_supply['S_T'],
            state_prev,
            theta,
            FPONE
        )
        
        # Planetary Multiplier
        mu_fp = compute_planetary_multiplier(X_fp, theta, FPONE)
        
        # Log-Prices
        prices = update_log_prices(
            scarcity_pressure['Phi_fp'],
            mu_fp,
            state_prev,
            theta,
            dac,
            FPONE
        )
        
        # Workforce
        workforce = update_workforce(
            scarcity_pressure['chi_fp'],
            prices['l_fp'],
            state_prev,
            theta,
            dac,
            FPONE
        )
        
        economic_state = {
            'B_T': backlog_supply['B_T'],
            'S_bar_T': backlog_supply['S_bar_T'],
            'chi_fp': scarcity_pressure['chi_fp'],
            'Phi_fp': scarcity_pressure['Phi_fp'],
            'X_fp': X_fp,
            'mu_fp': mu_fp,
            'l_fp': prices['l_fp'],
            'p_fp': prices['p_fp'],
            'L_fp': workforce['L_fp'],
            'pi_fp': workforce['pi_fp'],
        }

    # Step 12: Regulator
    sigma_fp = compute_branching_degree(horizon, FPONE)
    
    sigma_hat_fp = update_smoothed_branching(
        sigma_fp,
        state_prev.get('sigma_hat_fp', FPONE),
        theta['beta_fp'],
        FPONE
    )
    
    epsilon_fp = update_elasticity(
        sigma_hat_fp,
        state_prev.get('epsilon_fp', theta.get('epsilon_init_fp', FPONE)),
        theta['sigma_target_fp'],
        theta['kappa_P_fp'],
        theta['epsilon_min_fp'],
        theta['epsilon_max_fp'],
        FPONE
    )
    
    # Step 13: Finalize State
    state_new = {
        'epoch': T,
        'epsilon_fp': epsilon_fp,
        'sigma_hat_fp': sigma_hat_fp,
        'M_liq': M_liq,
        'agents': agents,
        'horizon_ids': sorted([e['id'] for e in horizon]),
        'horizon_events': {
            e['id']: {
                'R_fp': R_fp[e['id']],
                'DCD_fp': DCD_fp[e['id']],
                'alpha_stored': alpha_stored[e['id']]
            }
            for e in horizon
        },
        'dac': dac,  # Cache DAC
        **economic_state  # Merge economic state
    }
    
    # Compute state hash
    theta_hash = compute_theta_hash(theta)
    H_T = compute_state_hash(state_new, theta_hash)
    
    state_new['H_T'] = H_T
    
    print(f"Epoch {T} complete: H_T = {H_T[:16]}...")
    print(f"  B_T = {B_T}, M_T = {M_T}, M_liq = {M_liq}")
    print(f"  Agents: {len(agents)}, Horizon: {len(horizon)}")
    
    if SKUs:
        print(f"  Economic: {len(SKUs)} SKUs active")
    
    return state_new