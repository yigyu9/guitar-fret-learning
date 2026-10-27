"""Audit final-source tensors, fixed actor groups and raw/decision journals."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, '/home/ajou/yigyu/3')
import torch
from guitar_learning.training.training_log_io import iter_transitions

root=Path(__file__).resolve().parents[1]
support=root/'support'
manifest=json.loads((support/'source_manifest.json').read_text())
assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'] for r in manifest)
records=[]
for run,phase in [('smoke1024_final','F'),('resume1024_final','F'),('correlated_F3_final','F'),('support_R_final','R'),('joint_J_final','J')]:
    folder=root/run/phase
    a=torch.load(folder/'initial.pt',map_location='cpu',weights_only=False)
    b=torch.load(folder/'final.pt',map_location='cpu',weights_only=False)
    frozen=[key for key in a['model'] if (phase=='F' and (key.startswith(('support_encoder.','support_head.')) or key=='support_log_std')) or (phase=='R' and (key.startswith(('finger_encoder.','finger_heads.')) or key=='finger_log_std'))]
    assert all(torch.equal(a['model'][key],b['model'][key]) for key in frozen)
    def finite(value):
        if isinstance(value,torch.Tensor):return bool(torch.isfinite(value).all())
        if isinstance(value,dict):return all(finite(v) for v in value.values())
        if isinstance(value,(list,tuple)):return all(finite(v) for v in value)
        return True
    assert all(finite(b[key]) for key in ('model','actor_optimizer','value_optimizer'))
    report=json.loads((folder/'report.json').read_text())
    assert report['completed'] and report['lifecycle_verified'] and not report['changed_inputs'] and not report['missing_import_pins']
    raw=list(iter_transitions(folder/'transitions.jsonl.gz'))
    decisions=list(iter_transitions(folder/'decisions.jsonl.gz'))
    n=report['settings']['num_envs']; horizon=report['settings']['horizon']
    assert len(raw)*n==report['journal']['committed']
    assert len(decisions)==report['decision_journal']['committed']
    episodes=[json.loads(line)['episode'] for line in (folder/'episodes.jsonl').read_text().splitlines()]
    scope_valid=True
    for row in episodes:
        ledger=row['left_note_ledger'];mask=ledger['focus_mask']
        for key,values in ledger['values'].items():
            assert all(value==0 for value,selected in zip(values,mask) if not selected),(run,key)
        assert row['song']['denominator']==sum(mask)
        scope_valid &= row['finger_skill_diagnostics']['motion']['vector_sum_max_error_m'] < 1e-10
    assert scope_valid
    records.append(dict(run=run,phase=phase,completed=True,raw_control_transitions=report['journal']['committed'],
        decisions=len(decisions),duration_counts=dict(Counter(row['duration'] for row in decisions)),
        frozen_tensors_exact=len(frozen),all_model_optimizer_tensors_finite=True,
        completed_episodes=len(episodes),physical_failures=sum(row['reason']=='terminal_failure' for row in episodes),
        selected_note_scope_exact=True,material_point_vector_sum_exact=True,min_gpu_free_gib=report['min_cuda_free_bytes']/1024**3))
    if run=='correlated_F3_final':
        gamma=report['settings']['ppo']['gamma'];cgamma=report['settings']['ppo']['cost_gamma']
        max_reward=max_cost=0.
        covered=Counter()
        for row in decisions:
            start,end,env=row['start_control_tick'],row['end_control_tick'],row['env_id']
            assert end-start==row['duration'] and 1<=row['duration']<=row['planned_ticks']<=3
            assert start//horizon==(end-1)//horizon
            reward=sum(gamma**i*raw[t]['reward'][env] for i,t in enumerate(range(start,end)))
            cost=sum(cgamma**i*raw[t]['cost'][env] for i,t in enumerate(range(start,end)))
            max_reward=max(max_reward,abs(reward-row['discounted_reward']))
            max_cost=max(max_cost,abs(cost-row['discounted_cost']))
            for tick in range(start,end):covered[tick,env]+=1
        assert len(covered)==len(raw)*n and set(covered.values())=={1}
        assert max_reward<1e-5 and max_cost<1e-5,(max_reward,max_cost)
        records[-1]['discounted_raw_agreement']=dict(max_reward_error=max_reward,max_cost_error=max_cost,each_raw_transition_covered_once=True)
(support/'final_native_data_verification.json').write_text(json.dumps(dict(completed=True,records=records),indent=2)+'\n')
print(json.dumps(records,indent=2),flush=True)
