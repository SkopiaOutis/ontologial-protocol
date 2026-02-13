"""
TOP v3.1 - Metrics Extraction
"""

import csv
from typing import List, Dict, Any

def extract_metrics(states: List[Dict[str, Any]], theta: Dict[str, Any]) -> Dict[str, List]:
    """
    Extract all metrics from state history.
    
    Returns:
        Dict with lists of metrics over time
    """
    FPONE = theta['FPONE']
    
    metrics = {
        'epoch': [],
        'M_liq': [],
        'epsilon': [],
        'sigma_hat': [],
        'B_T': [],
        'M_T': [],
        'n_agents': [],
        'n_horizon': [],
        'gini': [],
        'balance_min': [],
        'balance_max': [],
        'balance_avg': [],
        'balance_std': [],
    }
    
    # Add economic metrics if available
    SKUs = theta.get('SKUs', [])
    if SKUs:
        for sku in SKUs:
            metrics[f'backlog_{sku}'] = []
            metrics[f'price_{sku}'] = []
            metrics[f'workforce_{sku}'] = []
    
    for state in states:
        T = state['epoch']
        
        # Basic metrics
        metrics['epoch'].append(T)
        metrics['M_liq'].append(state.get('M_liq', 0))
        metrics['epsilon'].append(state.get('epsilon_fp', 0) / FPONE)
        metrics['sigma_hat'].append(state.get('sigma_hat_fp', 0) / FPONE)
        
        # Would need to track B_T, M_T separately
        # For now, leave as 0
        metrics['B_T'].append(0)
        metrics['M_T'].append(0)
        
        # Agent metrics
        agents = state.get('agents', {})
        metrics['n_agents'].append(len(agents))
        
        balances = [a['E'] for a in agents.values()]
        if balances:
            metrics['balance_min'].append(min(balances))
            metrics['balance_max'].append(max(balances))
            metrics['balance_avg'].append(sum(balances) / len(balances))
            
            # Std dev
            avg = sum(balances) / len(balances)
            variance = sum((x - avg) ** 2 for x in balances) / len(balances)
            metrics['balance_std'].append(variance ** 0.5)
            
            # Gini
            metrics['gini'].append(compute_gini(balances))
        else:
            metrics['balance_min'].append(0)
            metrics['balance_max'].append(0)
            metrics['balance_avg'].append(0)
            metrics['balance_std'].append(0)
            metrics['gini'].append(0)
        
        # Horizon
        metrics['n_horizon'].append(len(state.get('horizon_ids', [])))
        
        # Economic metrics
        if SKUs:
            for sku in SKUs:
                backlog = state.get('B_T', {}).get(sku, 0)
                price_fp = state.get('p_fp', {}).get(sku, FPONE)
                workforce_fp = state.get('L_fp', {}).get(sku, FPONE // len(SKUs))
                
                metrics[f'backlog_{sku}'].append(backlog)
                metrics[f'price_{sku}'].append(price_fp / FPONE)
                metrics[f'workforce_{sku}'].append(workforce_fp / FPONE)
    
    return metrics

def save_to_csv(metrics: Dict[str, List], filepath: str):
    """Save metrics to CSV file."""
    if not metrics or 'epoch' not in metrics:
        return
    
    # Get all column names
    columns = list(metrics.keys())
    n_rows = len(metrics['epoch'])
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(columns)
        
        # Rows
        for i in range(n_rows):
            row = [metrics[col][i] for col in columns]
            writer.writerow(row)
    
    print(f"✓ Metrics saved to {filepath}")

def compute_gini(balances: List[int]) -> float:
    """Compute Gini coefficient."""
    if not balances or len(balances) < 2:
        return 0.0
    
    sorted_balances = sorted(balances)
    n = len(sorted_balances)
    
    cumsum = 0
    for i, x in enumerate(sorted_balances):
        cumsum += (2 * (i + 1) - n - 1) * x
    
    return cumsum / (n * sum(sorted_balances))