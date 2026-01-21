"""
THE ONTOLOGICAL PROTOCOL v3.2
Reference Implementation: Genesis Diagnosis (Shadow Run)

This module implements the core logic for the 'Shadow Run' phase.
It accepts Fiat-Economic data and re-evaluates it using Ontological Metrics
(Entropy, Thermodynamics, Lindy Effect).

Author: Skopia Outis
License: MIT
"""

import numpy as np
from typing import List, Dict, Any

class OntologicalPhysics:
    """
    Core physics engine for deriving endogenous parameters.
    """
    
    @staticmethod
    def get_thermodynamic_floor(burns: List[float]) -> float:
        """
        Calculates B_prod (Base Production Cost) as the 5th percentile 
        of transaction volumes. This represents the raw energy cost floor.
        """
        if not burns:
            return 0.0
        return float(np.percentile(burns, 5))

    @staticmethod
    def calculate_entropy_alpha(data_type: str) -> float:
        """
        Determines the Entropic Attribution (Alpha) based on structural density.
        
        In production, this would use: alpha = 1 - (LZMA_Size / Raw_Size)
        Here we simulate it with a structural mapping.
        """
        structure_map = {
            "PHYSICAL_CROP": 0.9,   # DNA (Extremely High Structure)
            "INFRASTRUCTURE": 0.8,  # Code/Math (High Structure)
            "SERVICE": 0.5,         # Labor (Medium Structure)
            "SPECULATION": 0.1      # Noise/Randomness (High Entropy)
        }
        return structure_map.get(data_type, 0.5)

def run_genesis_diagnosis(fiat_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Executes the Genesis Diagnosis on a dataset of fiat actors.
    
    Args:
        fiat_data: List of dicts with keys 'name', 'type', 'vol' (fiat volume).
        
    Returns:
        List of dicts with calculated 'Onto_Value'.
    """
    # 1. Endogenous Discovery of Thermodynamic Floor
    burns = [d['vol'] for d in fiat_data]
    b_prod = OntologicalPhysics.get_thermodynamic_floor(burns)
    
    diagnosis = []
    
    for actor in fiat_data:
        # 2. Measure Entropic Attribution (Alpha)
        # This replaces "Market Sentiment" with "Structural Reality".
        alpha = OntologicalPhysics.calculate_entropy_alpha(actor['type'])
        
        # 3. Calculate Ontological Value (The Re-Valuation)
        # Energy: Raw volume normalized by the floor.
        energy = actor['vol'] / b_prod if b_prod > 0 else 0
        
        # Lindy: Temporal persistence factor. 
        # Biological survival (Crops) has proven persistence > 2.0.
        lindy = 2.0 if actor['type'] == "PHYSICAL_CROP" else 1.0
        
        # The Formula: Value = Energy * Structure * Time
        val = energy * alpha * lindy
        
        diagnosis.append({
            "Name": actor['name'],
            "Fiat_Volume": actor['vol'],
            "Onto_Value": round(val, 2),
            "Alpha": alpha
        })
        
    return diagnosis

# --- Example Usage ---
if __name__ == "__main__":
    sample_economy = [
        {"name": "Hans (Farmer)", "type": "PHYSICAL_CROP", "vol": 5000},
        {"name": "Nexus (AI Dev)", "type": "INFRASTRUCTURE", "vol": 5000},
        {"name": "Bob (Daytrader)", "type": "SPECULATION", "vol": 50000}
    ]
    
    results = run_genesis_diagnosis(sample_economy)
    
    print(f"{'Actor':<20} | {'Fiat Vol':<10} | {'Onto Val':<10} | {'Alpha'}")
    print("-" * 55)
    for r in results:
        print(f"{r['Name']:<20} | {r['Fiat_Volume']:<10} | {r['Onto_Value']:<10} | {r['Alpha']}")
