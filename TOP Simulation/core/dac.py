"""
TOP v3.1 - Deterministic Arithmetic Contract (DAC)
Table-based log/exp for cross-platform consensus.
"""

from typing import List
from .primitives import check_i128, div_fp, mul_fp, clip, floor_div

def generate_log_table(
    x_min_fp: int,
    x_max_fp: int,
    N_log: int,
    FPONE: int
) -> List[int]:
    """Generate log lookup table using high-precision mpmath."""
    try:
        from mpmath import mp, log as mplog
    except ImportError:
        raise ImportError("mpmath required for DAC table generation. Install: pip install mpmath")
    
    mp.dps = 50
    
    if N_log < 2:
        raise ValueError(f"N_log must be >= 2, got {N_log}")
    
    delta_fp = (x_max_fp - x_min_fp) // (N_log - 1)
    if delta_fp <= 0:
        raise ValueError(f"Invalid log domain: x_min={x_min_fp}, x_max={x_max_fp}, N={N_log}")
    
    table = []
    for i in range(N_log):
        x_i_fp = x_min_fp + i * delta_fp
        
        # Convert to real
        x_real = mp.mpf(x_i_fp) / mp.mpf(FPONE)
        
        # Compute log
        log_real = mplog(x_real)
        
        # Convert back to fixed-point
        log_fp = int(log_real * FPONE)

        check_i128(log_fp, f"log_table[{i}]")
        table.append(log_fp)
    
    return table

def generate_exp_table(
    u_min_fp: int,
    u_max_fp: int,
    N_exp: int,
    FPONE: int
) -> List[int]:
    """Generate exp lookup table using high-precision mpmath."""
    try:
        from mpmath import mp, exp as mpexp
    except ImportError:
        raise ImportError("mpmath required for DAC table generation")
    
    mp.dps = 50
    
    if N_exp < 2:
        raise ValueError(f"N_exp must be >= 2, got {N_exp}")
    
    delta_fp = (u_max_fp - u_min_fp) // (N_exp - 1)
    if delta_fp <= 0:
        raise ValueError(f"Invalid exp domain: u_min={u_min_fp}, u_max={u_max_fp}, N={N_exp}")
    
    table = []
    for j in range(N_exp):
        u_j_fp = u_min_fp + j * delta_fp
        
        # Convert to real
        u_real = mp.mpf(u_j_fp) / mp.mpf(FPONE)
        
        # Compute exp
        exp_real = mpexp(u_real)
        
        # Convert back to fixed-point
        exp_fp = int(exp_real * FPONE)
        
        check_i128(exp_fp, f"exp_table[{j}]")
        table.append(exp_fp)
    
    return table

class DAC:
    """Deterministic Arithmetic Contract for log/exp."""
    
    def __init__(self, theta: dict):
        """
        Initialize DAC from Theta parameters.
        
        Args:
            theta: Dictionary containing:
                - FPONE
                - x_min_fp, x_max_fp, N_log
                - u_min_fp, u_max_fp, N_exp
                - log_table (optional, will generate if missing)
                - exp_table (optional, will generate if missing)
        """
        self.FPONE = theta['FPONE']
        
        # Log parameters
        self.x_min_fp = theta['x_min_fp']
        self.x_max_fp = theta['x_max_fp']
        self.N_log = theta['N_log']
        self.delta_log_fp = (self.x_max_fp - self.x_min_fp) // (self.N_log - 1)
        
        # Exp parameters
        self.u_min_fp = theta['u_min_fp']
        self.u_max_fp = theta['u_max_fp']
        self.N_exp = theta['N_exp']
        self.delta_exp_fp = (self.u_max_fp - self.u_min_fp) // (self.N_exp - 1)
        
        # Load or generate tables
        if 'log_table' in theta:
            self.log_table = theta['log_table']
        else:
            print("Generating log table...")
            self.log_table = generate_log_table(
                self.x_min_fp, self.x_max_fp, self.N_log, self.FPONE
            )
        
        if 'exp_table' in theta:
            self.exp_table = theta['exp_table']
        else:
            print("Generating exp table...")
            self.exp_table = generate_exp_table(
                self.u_min_fp, self.u_max_fp, self.N_exp, self.FPONE
            )
    
    def log_fp(self, x_fp: int) -> int:
        """
        Canonical logarithm function.
        
        Args:
            x_fp: Input (fixed-point)
        
        Returns:
            ln(x_fp) in fixed-point
        """
        # Step 1: Clamp
        x_clamped = clip(x_fp, self.x_min_fp, self.x_max_fp)
        
        # Step 2: Compute index
        i = floor_div(x_clamped - self.x_min_fp, self.delta_log_fp)
        
        # Step 3: Clamp index
        i = clip(i, 0, self.N_log - 2)
        
        # Step 4: Base grid point
        x_i = self.x_min_fp + i * self.delta_log_fp
        
        # Step 5: Fractional offset
        f_fp = div_fp(x_clamped - x_i, self.delta_log_fp, self.FPONE)
        
        # Step 6: Linear interpolation
        delta = self.log_table[i + 1] - self.log_table[i]
        result = self.log_table[i] + mul_fp(f_fp, delta, self.FPONE)

        print(f"    delta = {delta}")
        print(f"    result = {result}")
        
        return check_i128(result, "log_fp")
    
    def exp_fp(self, u_fp: int) -> int:
        """
        Canonical exponential function.
        
        Args:
            u_fp: Input (fixed-point)
        
        Returns:
            exp(u_fp) in fixed-point
        """
        # Step 1: Clamp
        u_clamped = clip(u_fp, self.u_min_fp, self.u_max_fp)
        
        # Step 2: Compute index
        j = floor_div(u_clamped - self.u_min_fp, self.delta_exp_fp)
        
        # Step 3: Clamp index
        j = clip(j, 0, self.N_exp - 2)
        
        # Step 4: Base grid point
        u_j = self.u_min_fp + j * self.delta_exp_fp
        
        # Step 5: Fractional offset
        f_fp = div_fp(u_clamped - u_j, self.delta_exp_fp, self.FPONE)
        
        # Step 6: Linear interpolation
        delta = self.exp_table[j + 1] - self.exp_table[j]
        result = self.exp_table[j] + mul_fp(f_fp, delta, self.FPONE)
        
        return check_i128(result, "exp_fp")