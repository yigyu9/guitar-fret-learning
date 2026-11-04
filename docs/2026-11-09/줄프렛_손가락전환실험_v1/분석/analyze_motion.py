"""원시 평가·학습 원장을 읽어 움직임/추종/노출/실패를 집계한다. 실험은 실행하지 않는다."""
import json,math,statistics,collections
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
RUN=BASE/'실행_v1';state=json.loads((RUN/'state.json').read_text())
rows=[]
def mean(values):return statistics.mean(values) if values else 0.
def load_episodes(path):return [json.loads(line)['episode'] for line in path.read_text().splitlines() if line]
for case,result in state['results'].items():
    jobs=state['jobs'];train=Path(jobs[case+'_train']['out'])/'J';evaluation=Path(jobs[case+'_evaluate']['out'])
    episodes=load_episodes(evaluation/'episodes.jsonl');training=load_episodes(train/'episodes.jsonl')
    # 담당 손가락은 명시적인 번들 입력에서 읽는다.
    mapping=json.loads((BASE/'입력/song_bundles'/case/'mapping/fingering.json').read_text())
    fingers=sorted(set(p['finger'] for p in mapping['presses']))
    indices=[i for f in fingers for i in range(5+4*(f-1),9+4*(f-1))]
    actual=[];requested=[];errors=[];actions=[];distances=[];aligned=[];holding=[]
    for e in episodes:
        motion=e['left_finger_motion']['values'];diag=e['finger_control_diagnostics']['values'];ledger=e['left_note_ledger']['values']
        actual.append(max(motion['actual_range_rad'][i] for i in indices)*180/math.pi)
        requested.append(max(motion['target_range_rad'][i] for i in indices)*180/math.pi)
        errors.append(mean([diag['applied_tracking_error_rad_rms'][i] for i in indices])*180/math.pi)
        actions.append(mean([motion['action_mean_abs'][i] for i in indices]))
        distances.extend(x*1000 for x,t in zip(ledger['surface_min'],ledger['exposure_time']) if t>0)
        phases=e['finger_progress']['phase_seconds'];aligned.extend(phases[f-1][2] for f in fingers);holding.extend(phases[f-1][4] for f in fingers)
    reasons=collections.Counter(r for e in training for r in e['failure_reasons'])
    trace=[]
    for e in training:
        trace.append(max(e['left_finger_motion']['values']['actual_range_rad'][i] for i in indices)*180/math.pi)
    n=len(training);failure=sum(e['reason']=='terminal_failure' for e in training)
    row=dict(case=case,eval_episodes=len(episodes),goal_fingers=fingers,
        eval_goal_joint_max_range_deg_mean=mean(actual),eval_goal_requested_max_range_deg_mean=mean(requested),
        eval_goal_tracking_rms_deg_mean=mean(errors),eval_goal_action_mean_abs=mean(actions),
        eval_goal_pad_min_distance_mm_mean=mean(distances),eval_goal_pad_min_distance_mm_min=min(distances),
        eval_aligned_seconds_mean=mean(aligned),eval_hold_seconds_mean=mean(holding),
        train_episodes=n,train_terminal_failure_count=failure,train_failure_reasons=dict(reasons),
        train_before_onset_count=sum(e['task_time_s']<3. for e in training),train_mean_duration_s=mean([e['task_time_s'] for e in training]),
        train_goal_joint_max_range_deg_mean=mean(trace),
        train_any_contact_episodes=sum(any(e['left_note_ledger']['values']['contact_done']) for e in training),
        train_any_clean_episodes=sum(any(x>0 for x in e['left_note_ledger']['values']['clean']) for e in training),
        train_any_achieved_episodes=sum(any(e['left_note_ledger']['values']['left']) for e in training),
        train_mean_reward=mean([e['reward'] for e in training]),train_mean_cost=mean([e['cost'] for e in training]))
    rows.append(row)
(BASE/'분석/움직임과실패_수치.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
for r in rows:print(json.dumps(r,ensure_ascii=False))
