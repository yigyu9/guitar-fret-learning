"""One declared timing comparison; unchanged original controller and strike gates."""
from pathlib import Path

from guitar_learning.tool.experiments.right_strike.native_probe import trajectory as original_trajectory
from guitar_learning.tool.experiments.right_strike_io_v2 import verify_manifest as io_verify

VARIANT = dict(schema='guitar_learning.right_strike_cross_timing.v1',
               approach_s=[.5, 2.6], cross_s=[2.94, 3.06], lift_s=[3.3, 3.8],
               thresholds='original', physics='original', active_axes='right6')


def verify_manifest(path, expected=None):
    data = io_verify(path, expected)
    if data.get('control_variant') != VARIANT:
        raise ValueError('Exactly the reviewed120ms crossing comparison required')
    if any(str(p.resolve()) not in data['pins'] for p in Path(__file__).parent.glob('*.py')):
        raise ValueError('Every protocol-v3 source must be pinned')
    return data


def trajectory(time_s, initial, waypoints):
    mapped = time_s
    if 2.9 <= time_s <= 3.3:
        mapped = min(3.1, max(2.9, 2.9+(time_s-2.94)/.12*.2))
    return original_trajectory(mapped, initial, waypoints)
