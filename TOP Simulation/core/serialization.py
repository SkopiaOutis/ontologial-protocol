"""
TOP v3.1 - Canonical Serialization and State Hash
"""

import hashlib
import struct
from typing import Dict, Any

def serialize_state(state: Dict[str, Any], theta_hash: bytes) -> bytes:
    """
    Canonical state serialization.
    
    Args:
        state: State dict containing all fields
        theta_hash: Raw 32-byte SHA-256 of Theta
    
    Returns:
        Canonical serialized bytes
    """
    parts = []
    
    # Header
    magic = b"TOPv3.1#"  # 8 bytes
    version = struct.pack('<I', 1)  # u32LE = 1
    epoch = struct.pack('<I', state['epoch'])  # u32LE
    
    parts.append(magic)
    parts.append(version)
    parts.append(epoch)
    parts.append(theta_hash)  # 32 bytes
    
    # Global Scalars (3 x i128 = 48 bytes)
    parts.append(i128_to_bytes(state['epsilon_fp']))
    parts.append(i128_to_bytes(state['sigma_hat_fp']))
    parts.append(i128_to_bytes(state['M_liq']))
    
    # Agent Table
    agents = state.get('agents', {})
    agent_ids = sorted(agents.keys())
    parts.append(struct.pack('<I', len(agent_ids)))
    
    for agent_id in agent_ids:
        agent = agents[agent_id]
        parts.append(serialize_string(agent_id))
        parts.append(i128_to_bytes(agent['E']))
        parts.append(i128_to_bytes(agent.get('S_native', 0)))
        parts.append(i128_to_bytes(agent.get('S_coll', 0)))
        parts.append(i128_to_bytes(agent.get('rest', 0)))
    
    # Horizon ID List
    horizon_ids = sorted(state.get('horizon_ids', []))
    parts.append(struct.pack('<I', len(horizon_ids)))
    for hid in horizon_ids:
        parts.append(serialize_string(hid))
    
    # Horizon Event Table
    horizon_events = state.get('horizon_events', {})
    parts.append(struct.pack('<I', len(horizon_ids)))
    for hid in horizon_ids:
        he = horizon_events.get(hid, {})
        parts.append(serialize_string(hid))
        parts.append(i128_to_bytes(he.get('R_fp', 0)))
        parts.append(i128_to_bytes(he.get('DCD_fp', 0)))
        parts.append(i128_to_bytes(he.get('alpha_stored', 0)))
    
    # Economic Tables (minimal version - just placeholders)
    # For now, we'll skip Economic Module
    # When implemented, add: B_T, S_bar_T, l_fp, p_fp, L_fp, X_fp
    
    return b''.join(parts)

def i128_to_bytes(x: int) -> bytes:
    """
    Convert i128 to little-endian bytes.
    
    Args:
        x: Signed 128-bit integer
    
    Returns:
        16 bytes (little-endian two's complement)
    """
    # Python int.to_bytes handles two's complement
    return x.to_bytes(16, byteorder='little', signed=True)

def serialize_string(s: str) -> bytes:
    """
    Serialize string as: u32LE(length) || ASCII bytes.
    
    Args:
        s: ASCII string
    
    Returns:
        Serialized bytes
    """
    s_bytes = s.encode('ascii')
    length = struct.pack('<I', len(s_bytes))
    return length + s_bytes

def compute_state_hash(state: Dict[str, Any], theta_hash: bytes) -> str:
    """
    Compute canonical state hash H_T.
    
    Args:
        state: State dict
        theta_hash: Raw 32-byte Theta hash
    
    Returns:
        64-character hex string (SHA-256)
    """
    serialized = serialize_state(state, theta_hash)
    hash_bytes = hashlib.sha256(serialized).digest()
    return hash_bytes.hex()

def compute_theta_hash(theta: Dict[str, Any]) -> bytes:
    """
    Compute Theta hash (simplified for minimal version).
    
    Args:
        theta: Theta parameters
    
    Returns:
        32-byte SHA-256 hash
    """
    # For now, use JSON serialization (not fully canonical, but sufficient for testing)
    import json
    theta_json = json.dumps(theta, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(theta_json.encode('utf-8')).digest()