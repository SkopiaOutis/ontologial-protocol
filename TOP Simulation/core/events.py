"""
TOP v3.1 - Canonical Event Schema
"""

import hashlib
import json
from typing import List, Dict, Any

def compute_event_id(event: Dict[str, Any]) -> str:
    """
    Compute canonical event ID via SHA-256.
    
    Args:
        event: Event dictionary with fields:
            - epoch (int)
            - type (str)
            - signers (list of str)
            - parents (list of str)
            - burn (int)
            - [type-specific fields]
    
    Returns:
        64-character lowercase hex string
    """
    # Canonical serialization order
    data = {
        'epoch': event['epoch'],
        'type': event['type'],
        'signers': sorted(event.get('signers', [])),  # Sorted
        'parents': sorted(event.get('parents', [])),  # Sorted
        'burn': event.get('burn', 0),
    }
    
    # Type-specific fields
    if event['type'] == 'INVESTMINT':
        data['delta_s'] = event['delta_s']
    elif event['type'] == 'COLLATERAL_DEPOSIT':
        data['deposit'] = event['deposit']
    elif event['type'] in ['DEMAND', 'CONFIRM']:
        data['sku'] = event['sku']
        data['quantity'] = event['quantity']
    
    # Deterministic JSON (sorted keys)
    canonical_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    # SHA-256
    hash_bytes = hashlib.sha256(canonical_json.encode('utf-8')).digest()
    
    return hash_bytes.hex()

def validate_event_structure(event: Dict[str, Any]) -> bool:
    """
    Validate event has required fields.
    
    Returns:
        True if valid structure
    
    Raises:
        ValueError if invalid
    """
    required = ['epoch', 'type', 'signers', 'parents']
    for field in required:
        if field not in event:
            raise ValueError(f"Event missing required field: {field}")
    
    # Type-specific validation
    event_type = event['type']
    
    if event_type in ['STANDARD', 'DEMAND', 'CONFIRM']:
        if event.get('burn', 0) <= 0:
            raise ValueError(f"{event_type} event must have burn > 0")
    
    if event_type == 'INVESTMINT':
        if event.get('burn', 0) != 0:
            raise ValueError("INVESTMINT event must have burn = 0")
        if event.get('delta_s', 0) <= 0:
            raise ValueError("INVESTMINT event must have delta_s > 0")
        if len(event['signers']) != 1:
            raise ValueError("INVESTMINT event must have exactly 1 signer")
    
    if event_type == 'COLLATERAL_DEPOSIT':
        if event.get('burn', 0) != 0:
            raise ValueError("COLLATERAL_DEPOSIT event must have burn = 0")
        if event.get('deposit', 0) <= 0:
            raise ValueError("COLLATERAL_DEPOSIT event must have deposit > 0")
        if len(event['signers']) != 1:
            raise ValueError("COLLATERAL_DEPOSIT event must have exactly 1 signer")
    
    if event_type in ['DEMAND', 'CONFIRM']:
        if 'sku' not in event:
            raise ValueError(f"{event_type} event must have 'sku' field")
        if event.get('quantity', 0) <= 0:
            raise ValueError(f"{event_type} event must have quantity > 0")
    
    return True

def sort_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sort events lexicographically by (epoch, id).
    
    Args:
        events: List of event dicts (must have 'id' field)
    
    Returns:
        Sorted list
    """
    return sorted(events, key=lambda e: (e['epoch'], e['id']))