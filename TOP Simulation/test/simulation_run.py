"""
TOP v1.0 - Calibrated Simulation Run (SYBIL BREAK & PRICE FIX)
"""
import sys
import os
import csv
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.events import compute_event_id
from core.executor import execute_epoch

class ScientificLogger:
    def __init__(self, filename="simulation_data.csv"):
        self.filename = filename
        self.headers = ["Epoch", "Total_Burn", "Liquid_Supply", "Price_Food", "Backlog_Food", "Income_Hans", "Income_Sybil"]
        with open(self.filename, mode='w', newline='') as f:
            csv.writer(f).writerow(self.headers)

    def log(self, epoch, total_burn, m_liq, prices, backlogs, incomes):
        b_food = backlogs.get('food', 0) if isinstance(backlogs, dict) else 0
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                epoch, total_burn, m_liq, 
                prices.get("food", 0), b_food,
                incomes.get("hans", 0), incomes.get("sybil", 0)
            ])

def load_theta(filepath: str) -> dict:
    with open(filepath, 'r') as f: return yaml.safe_load(f)

def run_simulation():
    print(">>> STARTING FINAL SIMULATION")
    theta = load_theta('theta_minimal.yaml')
    FPONE = theta['FPONE']
    logger = ScientificLogger()

    # STATE SETUP
    state = {
        'epoch': 0,
        'epsilon_fp': theta['epsilon_init_fp'], 'sigma_hat_fp': theta['FPONE'], 'M_liq': 5000,
        'agents': {
            'hans': {'E': 2000, 'S_native': 0, 'S_coll': 0, 'rest': 0},
            'sybil': {'E': 2000, 'S_native': 0, 'S_coll': 0, 'rest': 0},
            'alice': {'E': 1000, 'S_native': 0, 'S_coll': 0, 'rest': 0},
            'bob':   {'E': 1000, 'S_native': 0, 'S_coll': 0, 'rest': 0}, # Bob ist bereit!
        },
        'horizon_ids': [], 'horizon_events': {},
        'B_T': {'food': 0, 'energy': 0}, 
        'S_bar_T': {'food': 100*FPONE, 'energy': 100*FPONE},
        'L_fp': {'food': FPONE//2, 'energy': FPONE//2}, 'l_fp': {'food': 0, 'energy': 0},
        'p_fp': {'food': FPONE, 'energy': FPONE}, 'X_fp': {'earth': 0},
    }

    log_history = []
    sybil_chain_id = None
    hans_last_id = None
    total_burn = 0

    for T in range(1, 51):
        candidates = []
        
        # PARENTS
        honest_parents = [hans_last_id] if hans_last_id else (state['horizon_ids'][-1:] if state['horizon_ids'] else [])

        # 1. HANS (Massive Production)
        # Quantity 400! Da er nur jedes 2. Mal Food macht (Avg 200), deckt das die 150 Demand.
        sku_target = 'food' if T % 2 != 0 else 'energy'
        candidates.append({
            'epoch': T, 'type': 'CONFIRM', 'signers': ['hans'],
            'parents': honest_parents, 'burn': 40,
            'sku': sku_target, 'quantity': 400 
        })

        # 2. SYBIL (Isolated Loop)
        candidates.append({
            'epoch': T, 'type': 'STANDARD', 'signers': ['sybil'],
            'parents': [sybil_chain_id] if sybil_chain_id else [], 'burn': 40
        })

        # 3. ALICE (Demand)
        demand = 80 if T < 25 else 150
        candidates.append({
            'epoch': T, 'type': 'DEMAND', 'signers': ['alice'],
            'parents': honest_parents, 'burn': 10, 'sku': 'food', 'quantity': demand
        })

        # 4. BOB (The Tie-Breaker!)
        # Bob macht auch Demand und referenziert Hans.
        # HANS hat jetzt 2 Kinder (Alice + Bob). SYBIL hat nur 1 (sich selbst).
        # Das bricht die Symmetrie!
        candidates.append({
            'epoch': T, 'type': 'DEMAND', 'signers': ['bob'],
            'parents': honest_parents, 'burn': 10, 'sku': 'food', 'quantity': 10
        })

        # EXECUTE
        for e in candidates:
            e['id'] = compute_event_id(e)
            if 'hans' in e['signers']: hans_last_id = e['id']
            if 'sybil' in e['signers']: sybil_chain_id = e['id']

        prev_E_hans = state['agents']['hans']['E']
        prev_E_sybil = state['agents']['sybil']['E']

        state = execute_epoch(theta, state, log_history, candidates, T)
        log_history.extend(candidates)

        total_burn += sum(c['burn'] for c in candidates)
        
        inc_hans = state['agents']['hans']['E'] - prev_E_hans + 40
        inc_sybil = state['agents']['sybil']['E'] - prev_E_sybil + 40
        
        p_food = state.get('p_fp', {}).get('food', FPONE) / FPONE
        
        logger.log(T, total_burn, state['M_liq'], {'food': p_food}, state.get('B_T', {}), {'hans': inc_hans, 'sybil': inc_sybil})
        
        print(f"Epoch {T}: Price={p_food:.2f} | Hans Inc={inc_hans} | Sybil Inc={inc_sybil}")

if __name__ == '__main__':
    run_simulation()