"""초기 모델의 실제 동작 동일성과 A 지급 조건만의 차이를 대조한다."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
V5 = HERE.parent
V4 = V5.parent/'index_release_reference_learning_v4'

def read(path):
    return json.loads(path.read_text())

def compare(name):
    old = V4/'runs'/name
    new = V5/'runs'/('fit_stochastic_actual' if name == 'fit_stochastic' else name)
    a, b = read(old/'evaluation.json'), read(new/'evaluation.json')
    mode = name == 'fit_stochastic'
    assert read(old/'acceptance.json')['stochastic'] == read(new/'acceptance.json')['stochastic'] == mode
    assert len(a['episodes']) == len(b['episodes']) == 128
    payouts = []
    for x, y in zip(a['episodes'], b['episodes']):
        assert x['env_id'] == y['env_id']
        for key in set(x)-{'reward','reward_components'}:
            assert x[key] == y[key], (name, x['env_id'], key)
        ledger = y['success_settlement']
        note = next(z for z in x['notes'] if z['source_index'] == 4)
        expected = .25*float(note['achieved'] and note['released'])
        assert ledger['settlement_paid'] == expected
        assert ledger['settlement_suppressed'] == 0
        assert ledger['settlement_removed_raw'] == .5*float(note['achieved'])
        for key, value in x['reward_components'].items():
            target = value-.25*float(note['achieved'])+expected if key == 'song_left_success' else value
            assert abs(target-y['reward_components'][key]) < 1e-7, (name, key, target)
        assert abs(y['reward']-(x['reward']-.25*float(note['achieved'])+expected)) < 2e-6
        payouts.append(expected)
    with np.load(old/'learning_control_env0.npz',allow_pickle=False) as x, np.load(new/'learning_control_env0.npz',allow_pickle=False) as y:
        for key in ('q','target','body_state','candidate','raw_goal_normalized','decoded_goal_rad'):
            np.testing.assert_array_equal(x[key],y[key])
        force = float(np.max(np.abs(x['net_body_force_n']-y['net_body_force_n'])))
    report = read(new/'learning_report.json')
    assert report['completed'] and report['closed'] and report['selected_reference_calls'] == 0
    freeze = read(new/'evaluation_freeze.json')
    assert freeze['model_optimizers_updates_frozen'] and freeze['checkpoint_frozen']
    return dict(attempts=128, complete_music_ledger_exact=True, actual_q_targets_body_candidates_NN_goals_exact=True,
        only_reward_term_changed='song_left_success', paid_A_attempts=sum(p > 0 for p in payouts),
        paid_A_total=sum(payouts), force_difference_max_N=force, freeze=True)

if __name__ == '__main__':
    result = {name:compare(name) for name in ('fit_deterministic','fit_stochastic')}
    paths = [Path(__file__).resolve()]
    for root in (V4,V5):
        for name in result:
            folder = 'fit_stochastic_actual' if root == V5 and name == 'fit_stochastic' else name
            paths.extend(root/'runs'/folder/file for file in ('evaluation.json','learning_control_env0.npz','learning_report.json','evaluation_freeze.json','acceptance.json'))
    result['input_sha256'] = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='input_sha256'}))
