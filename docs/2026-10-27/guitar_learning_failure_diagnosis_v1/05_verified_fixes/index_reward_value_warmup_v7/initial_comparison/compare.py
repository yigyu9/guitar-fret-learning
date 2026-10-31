"""가치망 보정 전후 초기 실제 동작·보상 원장 동일성을 검사한다."""
import hashlib
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
V7 = HERE.parent
V6 = V7.parent/'index_cost_prior_zero_v6'

def read(path): return json.loads(path.read_text())

def check(name,stochastic):
    folders = [v/'runs'/name for v in (V6,V7)]
    for folder in folders:
        acceptance,report,freeze = [read(folder/f) for f in ('acceptance.json','learning_report.json','evaluation_freeze.json')]
        assert acceptance['stochastic'] is stochastic and acceptance['checkpoint_updates'] == 0
        assert report['completed'] and report['closed'] and not report['failure'] and not report['cleanup_errors']
        assert not report['changed_inputs'] and not report['unpinned_project_sources']
        assert report['fit_steps'] == report['PPO_updates'] == report['selected_reference_calls'] == report['checkpoint_updates'] == 0
        assert report['initialization_fit_steps'] == 1000
        assert freeze['model_optimizers_updates_frozen'] and freeze['checkpoint_frozen']
        digest = hashlib.sha256((folder.parent/'fit/fit.pt').read_bytes()).hexdigest()
        assert freeze['checkpoint_sha_before'] == freeze['checkpoint_sha_after'] == digest
    old,new = [read(f/'evaluation.json') for f in folders]
    assert old['assigned_quotas'] == new['assigned_quotas'] == [1]*128
    for data in (old,new):
        assert sorted(e['env_id'] for e in data['episodes']) == list(range(128))
        assert all([n['source_index'] for n in e['notes']] == [4,7,8] and len(e['reward_components']) == 9 for e in data['episodes'])
    assert old['episodes'] == new['episodes']
    with np.load(folders[0]/'learning_control_env0.npz',allow_pickle=False) as a,np.load(folders[1]/'learning_control_env0.npz',allow_pickle=False) as b:
        for key in ('q','target','body_state','candidate','wrong','released','raw_goal_normalized','decoded_goal_rad','reward'):
            np.testing.assert_array_equal(a[key],b[key])
        force = float(np.max(np.abs(a['net_body_force_n']-b['net_body_force_n'])))
    return dict(attempts=128,note_attempts=384,stochastic=stochastic,
        all3=sum(e['achieved'] for e in new['episodes']),
        joint=sum(e['achieved'] and e['notes'][0]['released'] for e in new['episodes']),
        full_episode_ledger_nine_rewards_and_env0_physical_NN_trace_exact=True,
        force_max_difference_N=force,force_separate=True),folders

if __name__ == '__main__':
    result,paths = {},[Path(__file__).resolve()]
    for name,stochastic in [('fit_deterministic',False),('fit_stochastic',True)]:
        result[name],folders = check(name,stochastic)
        for folder in folders:
            paths.extend(folder/f for f in ('acceptance.json','evaluation.json','learning_control_env0.npz','learning_report.json','evaluation_freeze.json'))
            paths.append(folder.parent/'fit/fit.pt')
    result['input_sha256'] = {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (HERE/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='input_sha256'}))
