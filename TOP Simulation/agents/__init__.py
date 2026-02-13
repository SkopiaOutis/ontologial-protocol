"""
TOP v3.1 - Agent-Based Modeling
"""

from .base_agent import BaseAgent
from .rational_agent import RationalAgent
from .strategies import ProducerAgent, HoarderAgent, SpeculatorAgent, AttackerAgent
from .simulator import run_emergence, initialize_agents, compute_gini

__all__ = [
    'BaseAgent',
    'RationalAgent',
    'ProducerAgent',
    'HoarderAgent',
    'SpeculatorAgent',
    'AttackerAgent',
    'run_emergence',
    'initialize_agents',
    'compute_gini'
]