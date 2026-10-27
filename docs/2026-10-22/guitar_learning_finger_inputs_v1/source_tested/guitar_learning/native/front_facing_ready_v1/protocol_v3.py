"""닫힘 제어를 유지하고 재접촉 정착1초/측정5초를 분리하는 절대일정."""
from .protocol_v2 import ROOT,A,BASE,PHASE,PLAN,REFERENCE,REPEAT,CERTIFICATE,STRIKE_PHASE,STRIKE_REFERENCE,BASELINE_REFERENCE,CONFIG_REFERENCE,TASK_CHAIN,LEFT_PROXIMAL,LEFT_DISTAL,SETTLED_HOLD,SETTLED_PLAN
from .protocol_v2 import schedule as previous_schedule
PROTOCOL='front_initial_pose_ready_full_cycle_v3_regrasp_settle1'
REGRASP_SETTLE_PLAN=ROOT/'docs/plans/front_facing_ready_regrasp_settle_20261016.md'


def schedule(case):
    result=previous_schedule(case)
    result['settle']=None
    if case=='regrasp':
        result.update(seconds=43.,settle=[37.,38.],dwell=[38.,43.])
    elif case=='continuous':
        result.update(seconds=59.,settle=[49.,50.],dwell=[50.,55.])
        result['strike_starts'][-1]=55.
    return result
