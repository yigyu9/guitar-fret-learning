"""CPU 입력 계약 감사. 물리 실행·학습·기존 파일 수정을 하지 않는다."""
import hashlib
import json
from unittest.mock import patch
from pathlib import Path

import torch

from guitar_learning.gpu.compact_press_v4 import CompactPressV4Environment
from guitar_learning.gpu.compact_press_v3 import CompactPressV3Environment
from guitar_learning.gpu.finger_skill_environment import remaining_negative_budget
from guitar_learning.training.compact_press_v3 import CompactPressV3Policy
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.tests.test_compact_press_environment import SKILL
from guitar_learning.song.task import ScoreTask, ScoreTarget


def environment(pelvis=False, full=True, count=2):
    class Environment(CompactPressV4Environment):
        include_pelvis = pelvis
        reward_profile = 'combined'
    metadata, snapshot = fixture(count)
    env = Environment(metadata, bundle=BUNDLE, song=SONG, skill=SKILL, device='cpu')
    env.set_evaluation(True, full_song=full)
    observation = env.reset(range(count), snapshot)
    return env, observation


def main():
    torch.set_num_threads(1)
    result = {'scope': 'CPU tensor observation audit; no native reachability or training evidence'}
    for pelvis in (False, True):
        env, obs = environment(pelvis=pelvis)
        model = CompactPressV3Policy(env.contract['observation']['dimension'], contract=env.contract)
        with torch.no_grad():
            output = model.act(*(obs[k] for k in ('state','events','mask','priority_events','priority_mask')), deterministic=True)
        key = 'pelvis' if pelvis else 'default'
        result[key] = dict(state_dim=obs['state'].shape[-1], goals=list(obs['priority_events'].shape),
            general_goals=list(obs['events'].shape), action_dim=output['action'].shape[-1],
            blocks=env.contract['observation']['compact_press']['blocks'],
            state_finite=bool(torch.isfinite(obs['state']).all()), right_action_zero=bool((output['action'][:,33:] == 0).all()))
    env, obs = environment()
    first, end = env.contract['observation']['compact_press']['blocks']['v3_state']
    budget_column = first+4
    budget = remaining_negative_budget(env._score_time(), env.onset, env.end,
        env.finger_weights, env.focus_mask, env.note['performance_paid'], env.note['performance_settled'])
    result['budget_clip'] = dict(target_count=env.M, raw=budget.tolist(),
        normalized_observation=obs['state'][:,budget_column].tolist(), scale=float(env.scales[budget_column]),
        clipped=bool((budget > 10*env.scales[budget_column]).any()))
    # 입력 목표의 velocity는 실제 표면점 속도의 음수이며 atan2 각도 등 다른 입력과 구분한다.
    selected=env._finger_targets(env._score_time())
    indices=selected['indices'].flatten(1).clamp_min(0)
    expected=env.surface_velocity.gather(1,indices[...,None].expand(-1,-1,3))/.5
    valid=selected['valid'].flatten(1)
    result['default_goal_ranges'] = dict(fret_min=int(env.fret.min()), fret_max=int(env.fret.max()), max_note_duration_s=float((env.end-env.onset).max()), saturated_valid_goal_values=int(((obs['priority_events'].abs() >= 10) & obs['priority_mask'][...,None]).sum()))
    result['goal_velocity_remap'] = dict(max_abs_error=float((obs['priority_events'][...,9:12][valid]-expected[valid].clamp(-10,10)).abs().max()),
        meaning='negative physical pad point relative velocity in moving guitar frame (error-rate convention)')
    # 회복 경계는 목표 슬롯에 없으므로 동일 CPU 상태에서 내부 범위만 소거한다.
    env, obs = environment(full=False, count=4)
    original_recovery=env.recovery_mask.clone()
    matches=[]
    for tick in range(0,int(env.duration_ticks.max()),3):
        active=tick<env.duration_ticks
        env.clock[:]=tick*4
        env.recovery_mask.copy_(original_recovery)
        original=env.observation()
        before=env._finger_preparation(env._score_time())['standby_reward_gate'].clone()
        targets=env._finger_targets(env._score_time())['valid'][...,0]
        env.recovery_mask.copy_(env.focus_mask)
        after_obs=env.observation()
        after=env._finger_preparation(env._score_time())['standby_reward_gate']
        affected=(before-after).abs()>1e-7
        affected &= active[:,None]
        if affected.any():
            same=all(torch.equal(original[k],after_obs[k]) for k in original)
            row,finger=affected.nonzero()[0].tolist()
            matches.append(dict(local_time_s=tick/60, row=row,finger=finger+1,
                selected_target_count=int(env.focus_mask[row].sum()),
                hidden_boundary_count=int((original_recovery[row]&~env.focus_mask[row]).sum()),
                tracking_goal_valid=bool(targets[row,finger]),
                actual_gate_with_boundary=float(before[row,finger]), actual_gate_without_boundary=float(after[row,finger]),
                all_policy_observations_equal=same))
            if len(matches)==3: break
    env.recovery_mask.copy_(original_recovery)
    result['hidden_recovery_boundary_ablation'] = dict(examples=matches,
        limitation='same CPU state with hidden recovery scope ablated; proves missing explicit context, not two native reachable histories or learning causality')
    # 무효 목표의 NaN이 인코더 특징에 섞이는지 원문을 보존하며 확인한다.
    env, obs = environment()
    model=CompactPressV3Policy(452,contract=env.contract)
    payload=obs['priority_events'].clone(); payload[~obs['priority_mask']]=float('nan')
    with torch.no_grad():
        a=model.actor_encoder.features(obs['state'],obs['priority_events'],obs['priority_mask'])
        b=model.actor_encoder.features(obs['state'],payload,obs['priority_mask'])
    result['invalid_goal_mask'] = dict(features_equal=bool(torch.equal(a,b)), feature_shape=list(a.shape))
    task=ScoreTask((ScoreTarget('f15','f15',2,15,1,1,3.,3.5,2.9,3.,3.5),))
    with patch('guitar_learning.gpu.environment.make_task',return_value=task):
        env, obs = environment()
    result['fret15_validation'] = dict(accepted=True, normalized_fret=float(obs['priority_events'][0,0,1]), limitation='default song contains only frets4..12; this is an accepted-input counterexample, not current-run invalid fret evidence')
    result['reviewed_source_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in map(Path,[
        'guitar_learning/gpu/compact_press.py','guitar_learning/gpu/compact_press_v3.py',
        'guitar_learning/gpu/compact_press_v4.py','guitar_learning/gpu/environment.py',
        'guitar_learning/gpu/finger_skill_environment.py','guitar_learning/gpu/finger_reward.py',
        'guitar_learning/training/compact_press.py','guitar_learning/training/compact_press_v3.py'])}
    destination=Path(__file__).with_name('results.json')
    destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='reviewed_source_sha256'},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
