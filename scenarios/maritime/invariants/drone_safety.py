"""Formal invariants for maritime threat detection safety."""

from talking_trees.verification.invariants import tree_invariant


@tree_invariant(
    "drone_safety",
    "Drone dispatch NEVER occurs unless: classification=vessel AND "
    "radar_status=confirmed_track AND in_restricted_zone=true AND confidence>=0.85",
)
def drone_safety_check(trace):
    """The critical safety invariant for drone dispatch."""
    if trace.node_reached("dispatch_drone"):
        return (
            trace.node_returned("check_vessel_class", "SUCCESS")
            and trace.node_returned("check_radar_confirmed", "SUCCESS")
            and trace.node_returned("check_in_zone", "SUCCESS")
            and trace.node_returned("check_high_confidence", "SUCCESS")
        )
    return True
