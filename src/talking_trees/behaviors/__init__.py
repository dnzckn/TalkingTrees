"""Custom behaviors for TalkingTrees.

This module contains example custom behaviors that extend py_trees.
Users can create their own behaviors here and register them with the BehaviorRegistry.
"""

from talking_trees.behaviors.examples import CheckBattery, Log, Wait

__all__ = ["CheckBattery", "Log", "Wait"]
