"""
Test minimal TOP execution.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import yaml
from core.events import compute_event_id, sort_events
from core.executor import execute_epoch

def load_theta(filepath: str) -> dict:
    """Load Theta from YAML."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def test_minimal():
    """Test minimal 3-agent, 2-epoch scenario."""
    
    # Load Theta
    theta = load_theta('theta_minimal.yaml')
    
    print("=" * 60)
    print("TOP v3.1 - Minimal Test")
    print("=" * 60)
    
    # Genesis State (S_0)
    state_0 = {
        'epoch': 0,
        'epsilon_fp': theta['epsilon_init_fp'],
        'sigma_hat_fp': theta['FPONE'],
        'M_liq': 3000,
        'agents': {
            'alice': {'E': 1000, 'S_native': 0, 'S_coll': 0, 'rest': 0},
            'bob': {'E': 1000, 'S_native': 0, 'S_coll': 0, 'rest': 0},
            'charlie': {'E': 1000, 'S_native': 0, 'S_coll': 0, 'rest': 0},
        },
        'horizon_ids': [],
        'horizon_events': {},
        # Economic initial state
        'B_T': {'food': 100, 'energy': 50},
        'S_bar_T': {'food': theta['FPONE'], 'energy': theta['FPONE']},
        'L_fp': {'food': theta['FPONE'] // 2, 'energy': theta['FPONE'] // 2},
        'l_fp': {'food': 0, 'energy': 0},
        'X_fp': {'earth': 0},
    }
    
    # Initial empty log
    log = []
    
    # Epoch 1: Alice creates orphan event
    candidates_1 = [
        {
            'epoch': 1,
            'type': 'STANDARD',
            'signers': ['alice'],
            'parents': [],
            'burn': 100
        }
    ]
    
    # Compute IDs
    for e in candidates_1:
        e['id'] = compute_event_id(e)
    
    print("\n--- Epoch 1 ---")
    state_1 = execute_epoch(theta, state_0, log, candidates_1, 1)
    
    # Update log with accepted events
    log.extend(candidates_1)
    
    # Epoch 2: Bob and Charlie reference Alice
    candidates_2 = [
        {
            'epoch': 2,
            'type': 'STANDARD',
            'signers': ['bob'],
            'parents': [candidates_1[0]['id']],
            'burn': 50
        },
        {
            'epoch': 2,
            'type': 'STANDARD',
            'signers': ['charlie'],
            'parents': [candidates_1[0]['id']],
            'burn': 75
        }
    ]
    
    for e in candidates_2:
        e['id'] = compute_event_id(e)
    
    print("\n--- Epoch 2 ---")
    state_2 = execute_epoch(theta, state_1, log, candidates_2, 2)
    
    # Final Report
    print("\n" + "=" * 60)
    print("FINAL STATE (Epoch 2)")
    print("=" * 60)
    
    for agent_id in sorted(state_2['agents'].keys()):
        agent = state_2['agents'][agent_id]
        print(f"{agent_id:10s}: E = {agent['E']:10d}")
    
    print(f"\nM_liq = {state_2['M_liq']}")
    print(f"H_2 = {state_2['H_T']}")
    
    # Show economic state
    if 'B_T' in state_2:
        print("\nEconomic State:")
        for sku in theta['SKUs']:
            print(f"  {sku}:")
            print(f"    Backlog: {state_2['B_T'].get(sku, 0)}")
            print(f"    Price: {state_2['p_fp'].get(sku, 0) / theta['FPONE']:.4f}")
            print(f"    Workforce: {state_2['L_fp'].get(sku, 0) / theta['FPONE']:.4f}")
    
    print("\n✓ Test complete")

if __name__ == '__main__':
    test_minimal()