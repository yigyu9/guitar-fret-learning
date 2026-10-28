"""CPU prescribed labels through current prefix reward ledger; no native physics."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
DIAG=HERE.parents[1]
PREFIX=DIAG/'05_verified_fixes/low_effort_index_prefix_learning_v1'
CASES=('switch_all_clean','same_clean_A_still_candidate','A_clean_B_wrong','A_wrong_B_clean')
TERMS=('song_left_contact','song_clean_hold','song_left_success','song_wrong_press','song_performance_deficit')


def main():
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    torch.set_num_threads(1)
    source=PREFIX/'learning.py';s=importlib.util.spec_from_file_location('prefix_reward_arithmetic',source)
    extra=importlib.util.module_from_spec(s);sys.modules[s.name]=extra;s.loader.exec_module(extra)
    config=json.loads((PREFIX/'cpu_inputs/settings.json').read_text());metadata,snapshot=fixture(len(CASES))
    env=extra.PrefixLearningEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    env.reset(range(len(CASES)),snapshot);ids=[4,7,8];view=config['song']['short_learning']['view'];gamma=config['ppo']['gamma'];offset=view['score_offset_s']
    assert env.focus_mask.sum(-1).tolist()==[3]*len(CASES) and torch.equal(env.finger_weights[:,ids],torch.ones(len(CASES),3))
    env.candidate.zero_();env.previous_candidate.zero_();env.wrong.zero_();env.previous_wrong.zero_()
    targets=[env.task.targets[i] for i in ids];A,B,C=targets;dt=1/240.
    def labels(_):
        now=float(env._score_time()[0]);env.candidate.zero_();env.wrong.zero_()
        for row in range(len(CASES)):
            a=A.press_s<=now<=A.end_s+dt
            b=B.press_s<=now<=C.end_s+dt
            if row in (1,2):a=now>=A.press_s
            if row==2:b=False
            if row==3:a=False
            env.candidate[row,4]=a;env.candidate[row,7]=b;env.candidate[row,8]=b
            if row==2:
                env.wrong[row,7]=B.onset_s<=now<=B.end_s;env.wrong[row,8]=C.onset_s<=now<=C.end_s
            if row==3:env.wrong[row,4]=A.onset_s<=now<=A.end_s
    ticks=[];zeros=torch.zeros(len(CASES),39)
    with patch.object(env,'_snapshot',side_effect=labels),patch.object(env,'_safety'),patch.object(env,'_surface_potential',return_value=torch.zeros(len(CASES))):
        for _ in range(view['duration_ticks']):
            previous=torch.stack([env.episode_reward_terms[k].clone() for k in TERMS],-1)
            env.begin_control(zeros)
            for _ in range(4):env.substep(dict(snapshot,physics_step=env.clock+1))
            env.end_control();ticks.append((torch.stack([env.episode_reward_terms[k] for k in TERMS],-1)-previous).numpy())
    values=np.asarray(ticks,dtype=np.float64);time=np.arange(1,len(values)+1)/60.;discount=gamma**np.arange(len(values));at_Aend=gamma**(np.arange(len(values))-(A.end_s-offset)*60)
    rows=[]
    for i,name in enumerate(CASES):
        total=values[:,i].sum(0);discounted=(discount[:,None]*values[:,i]).sum(0)
        rows.append(dict(case=name,undiscounted=dict(zip(TERMS,total.tolist())),discounted_from_reset=dict(zip(TERMS,discounted.tolist())),
            sum5=float(total.sum()),discounted_sum5=float(discounted.sum()),future5_at_Aend=float((at_Aend[time>A.end_s-offset,None]*values[time>A.end_s-offset,i]).sum()),
            achieved=env.note['left'][i,ids].tolist(),released=env.note['released'][i,ids].tolist(),
            payout_times={k:time[np.abs(values[:,i,j])>1e-8].tolist() for j,k in enumerate(TERMS)}))
    assert not rows[2]['released'][0]
    assert np.array_equal(values[:,0],values[:,1]) and rows[0]['released'][0] and not rows[1]['released'][0]
    assert rows[0]['sum5']>rows[2]['sum5'] and rows[0]['sum5']>rows[3]['sum5']
    assert rows[0]['discounted_sum5']>max(r['discounted_sum5'] for r in rows[2:])
    actual={}
    for u in (0,50,100,150,200,250,300):
        evaluation=json.loads((PREFIX/('evaluation_%06d'%u)/'evaluation.json').read_text());episodes=evaluation['episodes']
        e0=next(r for r in episodes if r['env_id']==0)
        actual[str(u)]=dict(note_achieved=[sum(r['notes'][j]['achieved'] for r in episodes) for j in range(3)],all3=sum(r['achieved'] for r in episodes),
            A_released=sum(r['notes'][0]['released'] for r in episodes),env0_reward9=e0['reward_components'],env0_sum5=sum(e0['reward_components'][k] for k in TERMS))
    delays={name:dict(delay_s=t-A.end_s,gamma60_weight=gamma**(60*(t-A.end_s)),GAE_residual_weight=(gamma*config['ppo']['gae_lambda'])**(60*(t-A.end_s)))
            for name,t in (('A_release_deadline',A.end_s+.1),('B_shared_press',B.press_s),('B7_onset',B.onset_s),('B8_onset',C.onset_s))}
    # Standby eligibility only: no physical posture/naturalness inference.
    gates=[]
    from guitar_learning.gpu.finger_reward import finger_preparation_gate
    for t in (A.end_s+.1,(A.end_s+B.press_s)/2,(B.end_s+C.onset_s)/2):
        gate=finger_preparation_gate(torch.full((len(CASES),),t,dtype=torch.float64),env.onset,env.end,env.press,env.finger,
            torch.zeros(len(CASES),4,dtype=torch.bool),torch.zeros(len(CASES),env.M),target_mask=env.recovery_mask)
        gates.append(dict(score_time_s=t,index_idle_gate=float(gate['gate'][0,0])))
    paths=[Path(__file__),PREFIX/'learning.py',PREFIX/'cpu_inputs/settings.json',PREFIX/'learning_analysis/results_v1/review.json',PREFIX/'learning_analysis/results_v1/INTERPRETATION.md',
        HERE.parent/'reward_objective_audit/results.json',HERE.parent/'reward_objective_audit/review.json',
        *[PREFIX/('evaluation_%06d'%u)/'evaluation.json' for u in (0,50,100,150,200,250,300)],
        *[ROOT/p for p in ('guitar_learning/gpu/environment.py','guitar_learning/gpu/simplified_finger_environment.py','guitar_learning/gpu/finger_reward.py','guitar_learning/gpu/finger_skill_environment.py','guitar_learning/training/decision_ppo.py')]]
    result=dict(CPU_only=True,GPU_executed=False,scope='Prescribed candidate/wrong through original substep/end_control/settlement; no geometry, dynamics, PBRS, standby/thumb/action comparison; no actual240Hz reconstruction',
        gamma=gamma,gae_lambda=config['ppo']['gae_lambda'],duration_ticks=len(values),required_clean_s=env.required[ids].tolist(),balance_b=[1.,1.,1.],source_indices=ids,source_targets=view['source_targets'],score_offset_s=offset,
        cases=rows,delays_from_Aend=delays,standby_gate_only=gates,actual_evaluations=actual,
        assertions=dict(release_neutral_same_labels_exact=True,full3_better_than_partial_undiscounted_and_discounted=True,B_shared_press_identical=B.press_s==C.press_s),
        input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    with (HERE/'results.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(rows=[{k:r[k] for k in ('case','sum5','discounted_sum5','future5_at_Aend','achieved','released')} for r in rows],delays=delays,gates=gates)))


if __name__=='__main__':main()
