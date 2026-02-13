"""
TOP v3.1 - Emergent Simulation Runner
"""

from typing import Dict, Any, List
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.executor import execute_epoch
from core.events import compute_event_id
from .strategies import ProducerAgent, HoarderAgent, SpeculatorAgent, AttackerAgent

def create_agent(agent_id: str, strategy: str):
    """Factory function to create agents."""
    if strategy == 'producer':
        return ProducerAgent(agent_id)
    elif strategy == 'hoarder':
        return HoarderAgent(agent_id)
    elif strategy == 'speculator':
        return SpeculatorAgent(agent_id)
    elif strategy == 'attacker':
        return AttackerAgent(agent_id, attack_type='burn_spam')
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

def initialize_agents(
    n_agents: int,
    strategy_mix: Dict[str, float]
) -> List[Any]:
    """
    Initialize agent population.
    
    Args:
        n_agents: Total number of agents
        strategy_mix: Dict like {'producer': 0.6, 'hoarder': 0.3, 'speculator': 0.1}
    
    Returns:
        List of agent instances
    """
    agents = []
    
    # Validate strategy_mix
    total = sum(strategy_mix.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"Strategy mix must sum to 1.0, got {total}")
    
    # Assign strategies proportionally
    agent_idx = 0
    for strategy, fraction in strategy_mix.items():
        count = int(n_agents * fraction)
        
        for i in range(count):
            agent_id = f"{strategy}_{agent_idx:04d}"
            agents.append(create_agent(agent_id, strategy))
            agent_idx += 1
    
    # Fill remainder with producers
    while agent_idx < n_agents:
        agent_id = f"producer_{agent_idx:04d}"
        agents.append(create_agent(agent_id, 'producer'))
        agent_idx += 1
    
    return agents

def run_emergence(
    theta: Dict[str, Any],
    n_agents: int = 100,
    n_epochs: int = 100,
    strategy_mix: Dict[str, float] = None,
    initial_balance: int = 1000,
    verbose: bool = True
) -> List[Dict[str, Any]]:
    """
    Run emergent simulation.
    
    Args:
        theta: Protocol parameters
        n_agents: Number of agents
        n_epochs: Number of epochs to simulate
        strategy_mix: Agent strategy distribution
        initial_balance: Starting balance per agent
        verbose: Print progress
    
    Returns:
        List of states (one per epoch)
    """
    if strategy_mix is None:
        strategy_mix = {
            'producer': 0.6,
            'hoarder': 0.2,
            'speculator': 0.15,
            'attacker': 0.05
        }
    
    # Initialize agents
    agents = initialize_agents(n_agents, strategy_mix)
    
    if verbose:
        print("=" * 60)
        print(f"EMERGENT SIMULATION: {n_agents} agents, {n_epochs} epochs")
        print("=" * 60)
        for strategy, fraction in strategy_mix.items():
            count = int(n_agents * fraction)
            print(f"  {strategy:12s}: {count:3d} agents ({fraction*100:.1f}%)")
        print()
    
    # Genesis state
    FPONE = theta['FPONE']
    SKUs = theta.get('SKUs', [])
    
    agent_states = {
        agent.agent_id: {
            'E': initial_balance,
            'S_native': 0,
            'S_coll': 0,
            'rest': 0
        }
        for agent in agents
    }
    
    state = {
        'epoch': 0,
        'epsilon_fp': theta.get('epsilon_init_fp', FPONE),
        'sigma_hat_fp': FPONE,
        'M_liq': n_agents * initial_balance,
        'agents': agent_states,
        'horizon_ids': [],
        'horizon_events': {}
    }
    
    # Economic initial state (if enabled)
    if SKUs:
        state['B_T'] = {sku: 100 for sku in SKUs}
        state['S_bar_T'] = {sku: FPONE for sku in SKUs}
        state['L_fp'] = {sku: FPONE // len(SKUs) for sku in SKUs}
        state['l_fp'] = {sku: 0 for sku in SKUs}
        state['X_fp'] = {p: 0 for p in theta.get('Planets', [])}
    
    log = []
    states = [state]
    
    # Run epochs
    for T in range(1, n_epochs + 1):
        # Generate candidate events from agent decisions
        candidates = []
        
        for agent in agents:
            # Agent decides action
            event = agent.decide_action(state, theta, log[-theta['H']:] if log else [])
            
            if event is not None:
                # Add epoch
                event['epoch'] = T
                
                # Compute ID
                event['id'] = compute_event_id(event)
                
                candidates.append(event)
        
        # Execute epoch
        if verbose and T % 10 == 0:
            print(f"Epoch {T}: {len(candidates)} candidate events")
        
        state = execute_epoch(theta, state, log, candidates, T)
        
        # Update log (only validated events)
        # For now, assume all candidates were validated (simplified)
        log.extend(candidates)
        
        states.append(state)
    
    if verbose:
        print("\n" + "=" * 60)
        print("SIMULATION COMPLETE")
        print("=" * 60)
        print(f"Final M_liq: {state['M_liq']}")
        print(f"Final epsilon: {state['epsilon_fp'] / FPONE:.4f}")
        
        # Agent statistics
        balances = [a['E'] for a in state['agents'].values()]
        print(f"\nAgent Balances:")
        print(f"  Min: {min(balances)}")
        print(f"  Max: {max(balances)}")
        print(f"  Avg: {sum(balances) / len(balances):.0f}")
        
        # Gini coefficient
        gini = compute_gini(balances)
        print(f"  Gini: {gini:.3f}")
    
    return states

def compute_gini(balances: List[int]) -> float:
    """Compute Gini coefficient of inequality."""
    if not balances or len(balances) < 2:
        return 0.0
    
    sorted_balances = sorted(balances)
    n = len(sorted_balances)
    
    cumsum = 0
    for i, x in enumerate(sorted_balances):
        cumsum += (2 * (i + 1) - n - 1) * x
    
    return cumsum / (n * sum(sorted_balances))