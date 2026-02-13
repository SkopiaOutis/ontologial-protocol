"""
TOP v3.1 - Horizon Construction and Canonical Kahn Algorithm
"""

from typing import List, Dict, Any, Set

def construct_horizon(log: List[Dict[str, Any]], T: int, H: int) -> List[Dict[str, Any]]:
    """
    Construct horizon H_T.
    
    Args:
        log: Complete accepted event log L (all epochs)
        T: Current epoch
        H: Horizon parameter
    
    Returns:
        List of events in horizon (unsorted)
    """
    T_min = max(0, T - H + 1)
    
    horizon = []
    for event in log:
        if T_min <= event['epoch'] <= T:
            horizon.append(event)
    
    return horizon

def canonical_kahn(horizon: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Canonical Kahn topological sort.
    
    Args:
        horizon: List of events in H_T
    
    Returns:
        Topologically sorted list (children before parents)
        
    Raises:
        ValueError if cycle detected
    """
    # Build adjacency structures
    event_map = {e['id']: e for e in horizon}
    
    # Compute in-degree
    indegree = {e['id']: 0 for e in horizon}
    children = {e['id']: [] for e in horizon}
    
    for event in horizon:
        event_id = event['id']
        for parent_id in event.get('parents', []):
            if parent_id in event_map:  # Only parents in horizon
                indegree[event_id] += 1
                children[parent_id].append(event_id)
    
    # Sort children lists lexicographically
    for parent_id in children:
        children[parent_id].sort()
    
    # Initialize zero-indegree set (sorted)
    Z = sorted([eid for eid, deg in indegree.items() if deg == 0])
    
    L = []
    
    while Z:
        # Remove lexicographically smallest
        event_id = Z.pop(0)
        L.append(event_map[event_id])
        
        # Process children in sorted order
        for child_id in children[event_id]:
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                # Insert into Z maintaining sorted order
                Z.append(child_id)
                Z.sort()
    
    # Check for cycles
    if len(L) != len(horizon):
        raise ValueError(f"DAG violation: cycle detected. Processed {len(L)}/{len(horizon)} events")
    
    # Reverse for RippleOrder (children before parents)
    L.reverse()
    
    return L