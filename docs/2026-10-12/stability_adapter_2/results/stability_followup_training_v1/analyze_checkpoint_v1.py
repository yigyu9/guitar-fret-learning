"""Compare a completed periodic evaluation with CP1; do not touch the live learner."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import torch

P = Path(__file__).resolve().parent
Q = P.parent/'stability_support_nominal_v1'
RUN = Q/'long_on_v1'
inputs = {}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    path = Path(path); inputs[str(path)] = sha(path)
    return json.loads(path.read_text())
def load(path):
    inputs[str(path)] = sha(path)
    return torch.load(path, map_location='cpu', weights_only=True)
def longest(mask):
    best = current = 0
    for value in mask:
        current = current+1 if value else 0
        best = max(best, current)
    return best/60


def evaluate(base, abi):
    native = base/'native/episode_0001'
    outer = read(base/'report.json'); nr = read(native/'report.json')
    rows = read(native/'controls.json'); trace = read(native/'trace.json')
    initial = read(native/'initial_values.json'); capture = read(native/'media/capture.json')
    events = read(native/'joint_events.json'); crossings = read(native/'joint_crossings.json')
    music = read(native/'music_physics_samples.json')
    if not rows or len(trace) != len(rows)+1: raise ValueError('complete nonempty trace required')
    distance = np.linalg.norm([r['position_outside_m'] for r in rows], axis=1)
    time = np.array([r['physics_step']/240 for r in rows])
    position = np.array([r['position_W_m'] for r in trace])
    quaternion = np.array([r['quaternion_xyzw'] for r in trace])
    norms = np.linalg.norm(quaternion, axis=1)
    if np.any(norms < 1e-9): raise ValueError('invalid quaternion')
    quaternion = quaternion/norms[:,None]
    angle = 2*np.arccos(np.clip(np.abs(quaternion@quaternion[0]),0,1))
    actual = np.array([r['q_rad'] for r in trace]); velocity = np.array([r['qdot_rad_s'] for r in trace])
    nominal = np.array([r['nominal81_rad'] for r in rows])
    teacher = np.array([r['teacher_nominal81_rad'] for r in rows])
    requested = np.array([r['requested81_rad'] for r in rows]); final = np.array([r['final81_rad'] for r in rows])
    groups = np.array(abi['groups']); lo,hi,rates = [np.array(abi[k]) for k in ('lower','upper','rates')]
    caps = np.array([abi['residual_caps_rad'][g] for g in groups])
    preload = np.array(initial['preload']['bounded_targets_rad'])
    arm = groups=='arm'; thumb = np.array([n.startswith('LH:thumb') for n in abi['names']])
    nominal_caps = np.where(arm,.15,np.where(thumb,.10,np.inf))
    expected = np.clip(teacher,np.maximum(lo,preload-nominal_caps),np.minimum(hi,preload+nominal_caps))
    previous = np.vstack([initial['q_ref_rad'],final[:-1]])
    rounding = 2*np.spacing(np.maximum(np.abs(final),np.abs(previous)).astype(np.float32)).astype(float)+1e-10
    checks = {'evaluation_completed': outer['completed'], 'baseline_frozen': nr['baseline_weights_unchanged'],
        'no_forbidden_calls': not nr['forbidden_calls'], 'nominal_guard_exact': np.array_equal(nominal,expected),
        'caps_bounds_rates': bool(np.all(np.abs(requested-nominal)<=caps+1e-10) and np.all(final>=lo-1e-8)
            and np.all(final<=hi+1e-8) and np.all(np.abs(final-previous)<=rates/60+rounding)),
        'finite_recorded_states': bool(all(np.isfinite(a).all() for a in (distance,position,quaternion,actual,velocity))),
        'stride_control60': all(r['physics_step']==4*(i+1) for i,r in enumerate(rows)),
        'source_calls': all(nr['baseline_actor_calls'][k]==max(len(rows)-120,0) for k in ('Fret','Strike')),
        'actual_strap_calls': nr['strap_force_calls']==13*nr['physics_steps'],
        'video_endpoint': capture['frames'][-1]['physics_step']==nr['physics_steps'],
        'render_preserves_states': all(r['render_preserves_states'] for r in capture['frames']),
        'music_counts': len(music)==nr['physics_steps'] and len(events)==nr['settled_events']
            and sum(r['joint_success'] for r in events)==nr['joint_success_events']
            and sum(r['accepted'] for r in crossings)==nr['accepted_crossings']}
    for name,v in nr['videos'].items():
        inputs[v['path']] = sha(v['path']); checks['video_SHA_'+name]=inputs[v['path']]==v['sha256']
    displacement = np.linalg.norm(position-position[0],axis=1)
    summary = {'full_horizon_completed':nr['full_horizon_completed'],'stop_reason':nr['stop_reason'],
        'physics_seconds':nr['physics_seconds'],'control_steps':nr['control_steps'],'physics_steps':nr['physics_steps'],
        'safety_violation':nr['safety_violation'],'return':nr['return'],
        'outside_percent':100*float(np.mean(distance>0)), 'max_position_outside_norm_m':float(max(distance)),
        'mean_position_outside_norm_m':float(np.mean(distance)), 'outside_distance_integral_m_s':float(distance.sum()/60),
        'longest_outside_interval_s':longest(distance>0),
        'first_outside_above_10cm_s':float(time[np.flatnonzero(distance>.1)[0]]) if np.any(distance>.1) else None,
        'max_displacement_from_initial_root_m':float(max(displacement)),
        'max_SO3_rotation_from_initial_guitar_deg':float(np.degrees(max(angle))),
        'max_abs_recorded_control_endpoint_qdot_rad_s':float(np.max(np.abs(velocity))),
        'max_actual_joint_change_from_initial_rad_by_group':{g:float(np.max(np.abs(actual-actual[0])[:,groups==g])) for g in sorted(set(groups))},
        'joint_success_events':nr['joint_success_events'],'settled_events':nr['settled_events'],
        'accepted_crossings':nr['accepted_crossings'],'total_crossings':len(crossings),
        'crossing_reason_counts':dict(Counter(r['reason'] for r in crossings)),
        'physics_frames_with_diagnostic_press_cells':sum(bool(r['press_cells']) for r in music),
        'mean_fret_approach_quality':float(np.mean([r['fret_approach_quality'] for r in rows])),
        'mean_pick_target_distance_G_m':float(np.mean([r['pick_target_distance_G_m'] for r in rows])),
        'videos':nr['videos'],'frames':len(capture['frames'])}
    return summary,checks,initial


parser = argparse.ArgumentParser(); parser.add_argument('--label',required=True); args = parser.parse_args()
if not args.label.startswith('update_') or not args.label[7:].isdigit(): raise ValueError('periodic update label required')
inputs[str(Path(__file__).resolve())]=sha(__file__)
old = load(Q/'smoke_on_v2/checkpoints/update_000001.pt'); new = load(RUN/'checkpoints'/(args.label+'.pt'))
record = read(RUN/'evaluation_records'/(args.label+'.json'))
checks = {'new_checkpoint':new['updates']>old['updates'],'same_ABI':new['abi']==old['abi'],
    'child_exit_zero':record['returncode']==0 and not record['timed_out'],
    'RMS_frozen':all(torch.equal(v,new['model'][k]) for k,v in old['model'].items() if k.startswith('obs_rms.')),
    'actor_critic_changed':all(any(not torch.equal(v,new['model'][k]) for k,v in old['model'].items() if k.startswith(prefix)) for prefix in ('actor.','critic.'))}
raw = (RUN/'training.jsonl').read_bytes(); prefix=[]
for line in raw.splitlines(keepends=True):
    if not line.endswith(b'\n'):break
    row = json.loads(line)
    if row['update']<=new['updates']:prefix.append(line)
    else:break
with (P/'training_to_checkpoint_v1.jsonl').open('xb') as f:f.write(b''.join(prefix))
inputs[str(P/'training_to_checkpoint_v1.jsonl')]=sha(P/'training_to_checkpoint_v1.jsonl')
logs = [json.loads(s) for s in prefix]
checks['training_counter_sequence']=bool(logs) and [r['update'] for r in logs]==list(range(2,new['updates']+1)) and logs[-1]['transitions']==new['transitions']
checks['logged_KL_and_RMS']=all(r['ppo']['optimizer_steps']>0 and 0<=r['ppo']['final_analytic_kl']<=.02 and not r['ppo']['RMS_updated'] for r in logs)
evaluations={}; initials=[]
for name,base in [('CP1',Q/'smoke_on_v2/evaluations/update_000001'),('new_checkpoint',RUN/'evaluations'/args.label)]:
    summary,local,initial=evaluate(base,new['abi']);evaluations[name]=summary;initials.append(initial)
    checks.update({name+'_'+k:bool(v) for k,v in local.items()})
checks['same_initial_state_and_PD']=initials[0]['native_initial_state']==initials[1]['native_initial_state'] and initials[0]['PD_properties']==initials[1]['PD_properties']
closure=read(RUN/'attempt.json')['input_sha256'];checks['learner_inputs_still_unchanged']=all(sha(p)==h for p,h in closure.items())
checks['analysis_inputs_unchanged']=all(sha(p)==h for p,h in inputs.items())
episodes=logs[-1]['completed_episodes']
result={'utc':datetime.now(timezone.utc).isoformat(),'label':args.label,'checkpoint_updates':new['updates'],'transitions':new['transitions'],
    'new_updates_this_run':len(logs),'checks_passed':all(checks.values()),'checks':checks,'evaluations':evaluations,
    'training':{'completed_episodes':len(episodes),'episode_returns':[r['return'] for r in episodes],
        'safety_terminations':sum(r['safety_violation'] is not None for r in episodes),
        'music_successes':sum(r['joint_success_events'] for r in episodes),
        'max_rollout_KL':max(r['ppo']['final_analytic_kl'] for r in logs)},
    'input_sha256':inputs,'scope':'one completed periodic deterministic evaluation compared with CP1; stochastic training returns separate; guitar actor-root position box, not body-center naturalness; actual joints/qdot sampled at60Hz, music at240Hz; ongoing learning not sealed'}
with (P/'analysis_v1.json').open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False)
print(json.dumps({k:result[k] for k in ('label','checkpoint_updates','checks_passed','training')},ensure_ascii=False))
if not result['checks_passed']:raise SystemExit([k for k,v in checks.items() if not v])
