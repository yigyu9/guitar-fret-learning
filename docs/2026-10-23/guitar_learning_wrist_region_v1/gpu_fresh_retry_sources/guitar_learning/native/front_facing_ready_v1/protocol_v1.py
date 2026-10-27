"""Prospective fixed validation schedule for the current initial-pose requirements."""
from ..lower_body_release_v1.common import ROOT,A,BASE
PHASE=BASE/'front_facing_ready_v1'
PLAN=ROOT/'docs/plans/front_facing_ready_20261016.md'
PROTOCOL='front_initial_pose_ready_full_cycle_v1'
REFERENCE=BASE/'front_facing_pose_v1/native_static_v5'
REPEAT=BASE/'front_facing_pose_v1/native_repeat_v1'
CERTIFICATE=BASE/'front_facing_pose_v1/repeat_verification_v2.json'
STRIKE_PHASE=BASE/'front_facing_strike_v1'
STRIKE_REFERENCE=STRIKE_PHASE/'native_strike_v6'
BASELINE_REFERENCE=STRIKE_PHASE/'native_baseline_v6'
CONFIG_REFERENCE=STRIKE_PHASE/'inputs/baseline_v6.json'
TASK_CHAIN=('Pelvis','Torso','Spine','Chest','L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:palm')
LEFT_PROXIMAL=('L_Thorax','L_Shoulder')
LEFT_DISTAL=('L_Elbow','L_Wrist')

def schedule(case):
    cases={
      'baseline':dict(seconds=28.,strike_starts=[],release=None,free=None,approach=None,close=None,dwell=None),
      'repeat':dict(seconds=22.,strike_starts=[10.,14.,18.],release=None,free=None,approach=None,close=None,dwell=None),
      'release':dict(seconds=28.,strike_starts=[],release=[10.,13.],free=[13.,28.],approach=None,close=None,dwell=None),
      'free_strike':dict(seconds=28.,strike_starts=[15.,19.,23.],release=[10.,13.],free=[13.,28.],approach=None,close=None,dwell=None),
      'regrasp':dict(seconds=36.,strike_starts=[],release=[10.,13.],free=[13.,28.],approach=[28.,30.],close=[30.,31.],dwell=[31.,36.]),
      'continuous':dict(seconds=52.,strike_starts=[10.,14.,18.,27.,31.,35.,48.],release=[22.,25.],free=[25.,40.],approach=[40.,42.],close=[42.,43.],dwell=[43.,48.])}
    assert case in cases
    result=cases[case]
    return dict(case=case,**{k:(v.copy() if isinstance(v,list) else v) for k,v in result.items()})
