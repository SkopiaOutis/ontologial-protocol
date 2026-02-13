"""
TOP v3.1 - Base Agent Class
"""

from typing import Dict, Any, List, Optional
import random

class BaseAgent:
    """Abstract base class for autonomous agents."""
    
    def __init__(self, agent_id: str, strategy: str = 'balanced'):
        self.agent_id = agent_id
        self.strategy = strategy
        self.rng = random.Random(hash(agent_id))  # Deterministic per agent
    
    def decide_action(
        self,
        state: Dict[str, Any],
        theta: Dict[str, Any],
        horizon: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Decide what action to take this epoch.
        
        Returns:
            Event dict or None (rest this epoch)
        """
        raise NotImplementedError
    
    def choose_parents(
        self,
        horizon: List[Dict[str, Any]],
        state: Dict[str, Any],
        max_parents: int = 3
    ) -> List[str]:
        """
        Choose which events to reference as parents.
        
        Args:
            horizon: Available events in horizon
            state: Current state (contains DCD values)
            max_parents: Maximum parents to select
        
        Returns:
            List of parent event IDs
        """
        if not horizon:
            return []
        
        # Default: random selection
        k = min(max_parents, len(horizon))
        selected = self.rng.sample(horizon, k)
        return [e['id'] for e in selected]
    
    def can_afford(self, state: Dict[str, Any], burn_amount: int) -> bool:
        """Check if agent can afford to burn."""
        my_balance = state['agents'].get(self.agent_id, {}).get('E', 0)
        return my_balance >= burn_amount