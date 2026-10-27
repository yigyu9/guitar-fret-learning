"""Keep maintenance at16s; begin each isolated action after the17..22s hold."""
from .protocol_v3 import schedule as previous_schedule

PROTOCOL='front_initial_pose_ready_v4_postmaintenance_hold5'
SETTLED_HOLD=[17.,22.]


def schedule(case):
    assert case in ('baseline','repeat','release','free_strike','regrasp')
    result=previous_schedule(case)
    if case!='baseline':
        result['seconds']+=6.
        result['strike_starts']=[t+6. for t in result['strike_starts']]
        for key in ('release','free','approach','close','settle','dwell'):
            if result[key] is not None:result[key]=[t+6. for t in result[key]]
    return result
