"""
TOP v3.1 - Visualization
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
from typing import Dict, List, Any

def plot_time_series(metrics: Dict[str, List], output_path: str):
    """
    Plot key metrics over time.
    
    Creates 4 subplots:
    1. M_liq evolution
    2. Gini coefficient
    3. Epsilon (elasticity)
    4. Balance distribution (min/avg/max)
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    epochs = metrics['epoch']
    
    # Plot 1: M_liq
    axes[0, 0].plot(epochs, metrics['M_liq'], 'b-', linewidth=2)
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('M_liq')
    axes[0, 0].set_title('Liquid Supply Over Time')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Plot 2: Gini
    axes[0, 1].plot(epochs, metrics['gini'], 'r-', linewidth=2)
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('Gini Coefficient')
    axes[0, 1].set_title('Wealth Inequality Over Time')
    axes[0, 1].axhline(y=0.4, color='gray', linestyle='--', alpha=0.5, label='US ≈0.48')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # Plot 3: Epsilon
    axes[1, 0].plot(epochs, metrics['epsilon'], 'g-', linewidth=2)
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Epsilon (Elasticity)')
    axes[1, 0].set_title('Regulator Elasticity Over Time')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Plot 4: Balance distribution
    axes[1, 1].fill_between(
        epochs,
        metrics['balance_min'],
        metrics['balance_max'],
        alpha=0.3,
        label='Min-Max Range'
    )
    axes[1, 1].plot(epochs, metrics['balance_avg'], 'k-', linewidth=2, label='Average')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('Balance')
    axes[1, 1].set_title('Agent Balance Distribution')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Time series plot saved to {output_path}")

def plot_gini(metrics: Dict[str, List], output_path: str):
    """Plot detailed Gini coefficient evolution."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    epochs = metrics['epoch']
    gini = metrics['gini']
    
    ax.plot(epochs, gini, 'b-', linewidth=2, label='TOP v3.1')
    ax.axhline(y=0.48, color='red', linestyle='--', alpha=0.7, label='USA (2023)')
    ax.axhline(y=0.34, color='green', linestyle='--', alpha=0.7, label='Germany (2023)')
    ax.axhline(y=0.25, color='orange', linestyle='--', alpha=0.7, label='Denmark (2023)')
    
    ax.fill_between(epochs, 0, gini, alpha=0.2)
    
    ax.set_xlabel('Epoch', fontsize=12)
    ax.set_ylabel('Gini Coefficient', fontsize=12)
    ax.set_title('Wealth Inequality: TOP v3.1 vs Real-World Economies', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 0.6)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Gini plot saved to {output_path}")

def plot_network(metrics: Dict[str, List], output_path: str):
    """Plot network metrics (horizon size, agent count)."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    epochs = metrics['epoch']
    
    # Plot 1: Horizon size
    axes[0].plot(epochs, metrics['n_horizon'], 'purple', linewidth=2)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Horizon Size')
    axes[0].set_title('DAG Horizon Growth')
    axes[0].grid(True, alpha=0.3)
    
    # Plot 2: Agent count
    axes[1].plot(epochs, metrics['n_agents'], 'orange', linewidth=2)
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Active Agents')
    axes[1].set_title('Agent Population Over Time')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Network plot saved to {output_path}")

def plot_economic(metrics: Dict[str, List], skus: List[str], output_path: str):
    """Plot economic metrics (prices, backlog, workforce)."""
    if not skus:
        return
    
    fig, axes = plt.subplots(len(skus), 3, figsize=(15, 5 * len(skus)))
    
    if len(skus) == 1:
        axes = axes.reshape(1, -1)
    
    epochs = metrics['epoch']
    
    for i, sku in enumerate(skus):
        # Prices
        axes[i, 0].plot(epochs, metrics[f'price_{sku}'], 'b-', linewidth=2)
        axes[i, 0].set_xlabel('Epoch')
        axes[i, 0].set_ylabel('Price')
        axes[i, 0].set_title(f'{sku.capitalize()}: Price Evolution')
        axes[i, 0].grid(True, alpha=0.3)
        
        # Backlog
        axes[i, 1].plot(epochs, metrics[f'backlog_{sku}'], 'r-', linewidth=2)
        axes[i, 1].set_xlabel('Epoch')
        axes[i, 1].set_ylabel('Backlog')
        axes[i, 1].set_title(f'{sku.capitalize()}: Backlog')
        axes[i, 1].grid(True, alpha=0.3)
        
        # Workforce
        axes[i, 2].plot(epochs, metrics[f'workforce_{sku}'], 'g-', linewidth=2)
        axes[i, 2].set_xlabel('Epoch')
        axes[i, 2].set_ylabel('Workforce Allocation')
        axes[i, 2].set_title(f'{sku.capitalize()}: Workforce')
        axes[i, 2].set_ylim(0, 1)
        axes[i, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✓ Economic plot saved to {output_path}")