"""
TOP v3.1 - Agent Strategy Variants
"""

from .rational_agent import RationalAgent

class ProducerAgent(RationalAgent):
    """Agent focused on production (CONFIRM events)."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id,
            strategy='producer',
            risk_aversion=0.3,  # Aggressive
            production_bias=0.9  # Almost always produce
        )

class HoarderAgent(RationalAgent):
    """Agent that minimizes burn, accumulates stasis."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id,
            strategy='hoarder',
            risk_aversion=0.9,  # Very conservative
            production_bias=0.2  # Rarely produces
        )
    
    def decide_action(self, state, theta, horizon):
        """Hoarder strategy: only act if absolutely necessary."""
        my_balance = state['agents'].get(self.agent_id, {}).get('E', 0)
        
        # Only act if very wealthy (>1000) or very poor (<100)
        if 100 < my_balance < 1000:
            return None  # Rest and accumulate stasis
        
        return super().decide_action(state, theta, horizon)

class SpeculatorAgent(RationalAgent):
    """Agent focused on structural position (maximize DCD)."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id,
            strategy='speculator',
            risk_aversion=0.5,
            production_bias=0.5
        )
    
    def choose_parents(self, horizon, state, max_parents=3):
        """Always select maximum parents for structural connectivity."""
        if not horizon:
            return []
        
        horizon_events = state.get('horizon_events', {})
        
        # Sort by DCD (prefer high-value events)
        sorted_horizon = sorted(
            horizon,
            key=lambda e: horizon_events.get(e['id'], {}).get('DCD_fp', 0),
            reverse=True
        )
        
        # Always take max parents
        k = min(max_parents, len(sorted_horizon))
        selected = sorted_horizon[:k]
        
        return [e['id'] for e in selected]

class AttackerAgent(RationalAgent):
    """Agent attempting to exploit the protocol."""
    
    def __init__(self, agent_id: str, attack_type: str = 'burn_spam'):
        super().__init__(
            agent_id,
            strategy='attacker',
            risk_aversion=0.1,  # Very aggressive
            production_bias=0.5
        )
        self.attack_type = attack_type
    
    def decide_action(self, state, theta, horizon):
        """Execute attack strategy."""
        my_balance = state['agents'].get(self.agent_id, {}).get('E', 0)
        
        if self.attack_type == 'burn_spam':
            # Burn maximum possible
            burn = int(my_balance * 0.9)
            if burn < 10:
                return None
            
            return {
                'type': 'STANDARD',
                'signers': [self.agent_id],
                'parents': self.choose_parents(horizon, state),
                'burn': burn
            }
        
        elif self.attack_type == 'stasis_farm':
            # Never produce, only rest
            return None
        
        elif self.attack_type == 'price_manipulate':
            # DEMAND everything to spike prices
            SKUs = theta.get('SKUs', [])
            if not SKUs:
                return None
            
            sku = self.rng.choice(SKUs)
            
            return {
                'type': 'DEMAND',
                'signers': [self.agent_id],
                'parents': [],
                'burn': max(10, my_balance // 20),
                'sku': sku,
                'quantity': 1000  # Massive demand
            }
        
        else:
            return super().decide_action(state, theta, horizon)