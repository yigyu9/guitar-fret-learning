"""Increase only measured guitar-position/rotation costs in the frozen pilot."""
from .deadline_native_v1 import pilot_reward as base_reward

STABILITY_MULTIPLIER = 4.


def priority_reward(*args, **kwargs):
    _, ledger = base_reward(*args, **kwargs)
    ledger['position'] *= STABILITY_MULTIPLIER
    ledger['rotation_upper_proxy'] *= STABILITY_MULTIPLIER
    return float(sum(ledger.values())), ledger
