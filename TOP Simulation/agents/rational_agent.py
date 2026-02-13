"""
TOP v3.1 - Rational Economic Agent
"""

from typing import Dict, Any, List, Optional
from .base_agent import BaseAgent

class RationalAgent(BaseAgent):
    """Agent that makes decisions based on economic incentives."""
    
    def __init__(
        self,
        agent_id: str,
        strategy: str = 'balanced',
        risk_aversion: float = 0.5,
        production_bias: float = 0.6
    ):
        super().__init__(agent_id, strategy)
        self.risk_aversion = risk_aversion  # 0=aggressive, 1=conservative
        self.production_bias = production_bias  # probability to produce vs demand
    
    def decide_action(
        self,
        state: Dict[str, Any],
        theta: Dict[str, Any],
        horizon: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Rational decision based on:
        - Balance (can I afford?)
        - Prices (what's valuable?)
        - Scarcity (what's needed?)
        - Expected income (structural position)
        """
        FPONE = theta['FPONE']
        SKUs = theta.get('SKUs', [])
        
        # Get my state
        my_balance = state['agents'].get(self.agent_id, {}).get('E', 0)
        
        # Risk-adjusted burn amount
        max_burn = int(my_balance * (1 - self.risk_aversion))
        
        if max_burn < 10:  # Too poor to act
            return None
        
        # Decide burn amount (proportional to balance, risk-adjusted)
        burn_amount = min(max_burn, my_balance // 10)
        
        if not SKUs:
            # No economic module - just STANDARD event
            return {
                'type': 'STANDARD',
                'signers': [self.agent_id],
                'parents': self.choose_parents(horizon, state),
                'burn': burn_amount
            }
        
        # Economic decision: PRODUCE or DEMAND?
        if self.rng.random() < self.production_bias:
            # Produce highest-price SKU
            sku = self._choose_production_sku(state, theta)
            quantity = self._estimate_production(state, theta, sku)
            
            return {
                'type': 'CONFIRM',
                'signers': [self.agent_id],
                'parents': self.choose_parents(horizon, state),
                'burn': burn_amount,
                'sku': sku,
                'quantity': quantity
            }
        else:
            # Demand scarcest SKU
            sku = self._choose_demand_sku(state, theta)
            quantity = self._estimate_demand(state, theta, sku)
            
            return {
                'type': 'DEMAND',
                'signers': [self.agent_id],
                'parents': self.choose_parents(horizon, state),
                'burn': burn_amount,
                'sku': sku,
                'quantity': quantity
            }
    
    def _choose_production_sku(self, state: Dict[str, Any], theta: Dict[str, Any]) -> str:
        """Choose SKU with highest price (most profitable)."""
        SKUs = theta['SKUs']
        prices = state.get('p_fp', {})
        
        if not prices:
            return self.rng.choice(SKUs)
        
        # Produce highest-price SKU
        return max(SKUs, key=lambda s: prices.get(s, 0))
    
    def _choose_demand_sku(self, state: Dict[str, Any], theta: Dict[str, Any]) -> str:
        """Choose SKU with highest scarcity (most needed)."""
        SKUs = theta['SKUs']
        scarcity = state.get('chi_fp', {})
        
        if not scarcity:
            return self.rng.choice(SKUs)
        
        # Demand scarcest SKU
        return max(SKUs, key=lambda s: scarcity.get(s, 0))
    
    def _estimate_production(self, state: Dict[str, Any], theta: Dict[str, Any], sku: str) -> int:
        """Estimate how much we can produce."""
        # Simple: base on workforce allocation
        L_fp = state.get('L_fp', {}).get(sku, theta['FPONE'] // len(theta['SKUs']))
        A_fp = theta.get('A_fp', {}).get(sku, theta['FPONE'])
        
        # Capacity
        capacity_fp = (L_fp * A_fp) // theta['FPONE']
        capacity_base = capacity_fp // theta['FPONE']
        
        # Produce 50-100% of capacity (random variance)
        return max(1, int(capacity_base * self.rng.uniform(0.5, 1.0)))
    
    def _estimate_demand(self, state: Dict[str, Any], theta: Dict[str, Any], sku: str) -> int:
        """Estimate how much we need."""
        # Simple: proportional to backlog
        backlog = state.get('B_T', {}).get(sku, 0)
        
        # Demand 10-50% of backlog (random variance)
        return max(1, int(backlog * self.rng.uniform(0.1, 0.5)))
    
    def choose_parents(
        self,
        horizon: List[Dict[str, Any]],
        state: Dict[str, Any],
        max_parents: int = 3
    ) -> List[str]:
        """Strategic parent selection - prefer high DCD events."""
        if not horizon:
            return []
        
        horizon_events = state.get('horizon_events', {})
        
        # Sort by DCD (descending)
        sorted_horizon = sorted(
            horizon,
            key=lambda e: horizon_events.get(e['id'], {}).get('DCD_fp', 0),
            reverse=True
        )
        
        # Select top-DCD events
        k = min(max_parents, len(sorted_horizon))
        selected = sorted_horizon[:k]
        
        return [e['id'] for e in selected]