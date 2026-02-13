"""
Test emergent agent-based simulation.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import yaml
from agents.simulator import run_emergence

def load_theta(filepath: str) -> dict:
    """Load Theta from YAML."""
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def test_emergence():
    """Run emergent simulation."""
    
    theta = load_theta('theta_minimal.yaml')
    
    # Run 50 agents for 20 epochs (small test)
    states = run_emergence(
        theta,
        n_agents=50,
        n_epochs=20,
        strategy_mix={
            'producer': 0.6,
            'hoarder': 0.2,
            'speculator': 0.15,
            'attacker': 0.05
        },
        initial_balance=1000,
        verbose=True
    )
    
    # Extract and save metrics
    from analysis.extract import extract_metrics, save_to_csv
    from analysis.visualize import plot_time_series, plot_gini, plot_network, plot_economic
    
    metrics = extract_metrics(states, theta)
    
    # Save CSV
    save_to_csv(metrics, 'data/raw/emergence_test.csv')
    
    # Generate plots
    plot_time_series(metrics, 'data/figures/time_series.png')
    plot_gini(metrics, 'data/figures/gini.png')
    plot_network(metrics, 'data/figures/network.png')
    
    SKUs = theta.get('SKUs', [])
    if SKUs:
        plot_economic(metrics, SKUs, 'data/figures/economic.png')
    
    print("\n✓ Emergence test complete")
    print("✓ All data and figures saved")

if __name__ == '__main__':
    test_emergence()