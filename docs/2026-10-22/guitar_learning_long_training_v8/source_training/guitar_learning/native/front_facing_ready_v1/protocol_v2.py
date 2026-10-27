"""기존 기하 참조를 보존하고 최종보정 뒤 정지5초를 명시하는 절대시간 일정."""
from .protocol_v1 import ROOT,A,BASE,PHASE,PLAN,REFERENCE,REPEAT,CERTIFICATE,STRIKE_PHASE,STRIKE_REFERENCE,BASELINE_REFERENCE,CONFIG_REFERENCE,TASK_CHAIN,LEFT_PROXIMAL,LEFT_DISTAL
PROTOCOL='front_initial_pose_ready_full_cycle_v2_settled_hold5'
SETTLED_HOLD=[11.,16.]
SETTLED_PLAN=ROOT/'docs/plans/front_facing_ready_settled_hold_20261016.md'

def schedule(case):
    cases={
      'baseline':dict(seconds=28.,strike_starts=[],release=None,free=None,approach=None,close=None,dwell=None),
      'repeat':dict(seconds=28.,strike_starts=[16.,20.,24.],release=None,free=None,approach=None,close=None,dwell=None),
      'release':dict(seconds=34.,strike_starts=[],release=[16.,19.],free=[19.,34.],approach=None,close=None,dwell=None),
      'free_strike':dict(seconds=34.,strike_starts=[21.,25.,29.],release=[16.,19.],free=[19.,34.],approach=None,close=None,dwell=None),
      'regrasp':dict(seconds=42.,strike_starts=[],release=[16.,19.],free=[19.,34.],approach=[34.,36.],close=[36.,37.],dwell=[37.,42.]),
      'continuous':dict(seconds=58.,strike_starts=[16.,20.,24.,33.,37.,41.,54.],release=[28.,31.],free=[31.,46.],approach=[46.,48.],close=[48.,49.],dwell=[49.,54.])}
    assert case in cases
    result=cases[case]
    return dict(case=case,**{k:(v.copy() if isinstance(v,list) else v) for k,v in result.items()})
