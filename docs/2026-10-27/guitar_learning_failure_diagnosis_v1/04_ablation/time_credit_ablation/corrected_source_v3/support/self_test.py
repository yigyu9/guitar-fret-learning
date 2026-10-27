"""CPU-only actual-model initialization, GAE and strict variant-load checks."""
import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path
import pickle
import random
import tempfile

import numpy as np
import torch

from variants import VARIANTS,LONG_GAMMA,settings_for,policy_type
from run_variant import watched_sources
from guitar_learning.tool.experiments.short_finger_learning.runner import make_settings
from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPolicy,ShortEnvironment
from guitar_learning.training.decision_ppo import DecisionPPOTrainer,compute_decision_gae
from guitar_learning.training.ppo import PPOConfig
from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
from guitar_learning.gpu.thumb_support import load_thumb_support
from guitar_learning.gpu.episode_diagnostics import DIAGNOSTIC_CONTRACT


BASE=Path(__file__).resolve().parents[1]
DIAG=BASE.parents[2]


def read(path):return json.loads(path.read_text())


def differences(left,right,path=''):
    if isinstance(left,dict) and isinstance(right,dict):
        result=[]
        for key in left.keys()|right.keys():
            p=path+'.'+key if path else key
            if key not in left or key not in right:result.append(p)
            else:result.extend(differences(left[key],right[key],p))
        return sorted(result)
    return [] if left==right else [path]


def seed():
    random.seed(7);np.random.seed(7);torch.manual_seed(7)


def rng():
    return hashlib.sha256(pickle.dumps((random.getstate(),np.random.get_state()))+torch.get_rng_state().numpy().tobytes()).hexdigest()


def payload(trainer,settings):
    # Exact production identity/model/optimizer/RNG payload, CPU-only cuda_rng=None.
    return dict(identity=trainer._identity(),model=trainer.policy.state_dict(),
        actor_optimizer=trainer.actor_optimizer.state_dict(),value_optimizer=trainer.value_optimizer.state_dict(),
        cost_weight=trainer.cost_weight,updates=trainer.updates,metadata=dict(settings=settings),
        torch_rng=torch.get_rng_state(),numpy_rng=np.random.get_state(),python_rng=random.getstate(),cuda_rng=None)


def main():
    torch.set_num_threads(1)
    if torch.cuda.is_available():raise RuntimeError('CPU self-test requires CUDA_VISIBLE_DEVICES empty')
    active=read(BASE/'active_source_before.json')
    own=[*watched_sources(),DIAG/'02_contact_reward/teacher_fixed_B_export/metadata.json']
    pins={**active,**{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in own}}
    teacher=DIAG/'02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json'
    args=argparse.Namespace(teacher=str(teacher),mode='incremental',initial_std=.1711710544767014,
        song='05_BN2-131-B_solo',size='large',num_envs=128,horizon=32,updates=300,save_every=50,seed=7)
    baseline=make_settings(args)
    a,b=[settings_for(baseline,variant) for variant in VARIANTS]
    reference_checks=[]
    for settings in (baseline,a,b):
        reference=read_reference(DIAG/'03_short_learning/reference_middle_row8_v2.json',settings['song']['short_learning'])
        reference_checks.append(reference['source_target_id'])
    patch=load_thumb_support()
    assert patch['contract']['schema']=='guitar_learning.gpu_thumb_rear_support.v3'
    assert DIAGNOSTIC_CONTRACT['schema']=='guitar_learning.gpu_left_episode_diagnostics.v6'
    np.testing.assert_array_equal(patch['plane'],[0.,0.,-1.,-.008])
    diff_a=differences(baseline,a);diff_b=differences(baseline,b)
    assert diff_a==['ppo.gamma','song.short_learning.ablation','song.surface_approach_gamma']
    assert diff_b==['song.short_learning.ablation']
    assert a['ppo']['gamma']==a['song']['surface_approach_gamma']==LONG_GAMMA
    metadata=read(DIAG/'02_contact_reward/teacher_fixed_B_export/metadata.json')
    contracts=[]
    for settings in (baseline,a,b):
        env=ShortEnvironment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],
            skill=settings['finger_skill'],device='cpu',hand='left')
        assert env.approach_gamma==settings['ppo']['gamma']
        contracts.append(copy.deepcopy(env.contract))
    seed();base_policy=ShortPolicy(contract=contracts[0],size='large');base_rng=rng()
    seed();a_policy=policy_type(VARIANTS[0],fresh=True)(contract=contracts[1],size='large')
    assert rng()==base_rng and all(torch.equal(v,a_policy.state_dict()[k]) for k,v in base_policy.state_dict().items())
    del base_policy,a_policy
    seed();normal=ShortPolicy(contract=contracts[2],size='large');rng_normal=rng()
    seed();zero=policy_type(VARIANTS[1],fresh=True)(contract=contracts[2],size='large');rng_zero=rng()
    changed=[name for name,value in normal.state_dict().items() if not torch.equal(value,zero.state_dict()[name])]
    assert changed==['cost_critic.weight','cost_critic.bias'] and rng_normal==rng_zero
    assert bool((zero.cost_critic.weight==0).all()) and bool((zero.cost_critic.bias==0).all())
    seed();not_fresh=policy_type(VARIANTS[1],fresh=False)(contract=contracts[2],size='large')
    assert all(torch.equal(value,not_fresh.state_dict()[name]) for name,value in normal.state_dict().items())
    del normal,not_fresh
    trainer=DecisionPPOTrainer(zero,PPOConfig(**b['ppo']))
    observation=(torch.randn(8,561)*.01,torch.randn(8,2,24)*.01,torch.ones(8,2,dtype=torch.bool),
        torch.randn(8,8,24)*.01,torch.ones(8,8,dtype=torch.bool))
    before_encoder={name:v.clone() for name,v in zero.value_encoder.state_dict().items()}
    initial=zero(*observation)
    assert bool((initial['cost_value']==0).all())
    trainer.value_optimizer.zero_grad()
    ((initial['reward_value']-1).square().mean()+initial['cost_value'].square().mean()).backward()
    trainer.value_optimizer.step()
    assert any(not torch.equal(v,before_encoder[k]) for k,v in zero.value_encoder.state_dict().items())
    after=zero(*observation)['cost_value'].detach()
    assert bool((after==0).all())
    flags=torch.zeros(4,2,dtype=torch.bool);flags[-1]=True
    values=after.reshape(4,2);duration=torch.ones(4,2,dtype=torch.long);valid=torch.ones(4,2,dtype=torch.bool)
    gae=compute_decision_gae(torch.zeros_like(values),values,values,flags,torch.zeros_like(flags),duration,valid,1.,.98)[0]
    assert bool((gae==0).all())
    # A real positive target can train the still-trainable zero cost head.
    trainer.value_optimizer.zero_grad()
    prediction=zero(*observation)['cost_value'];loss=(prediction-1).square().mean();loss.backward()
    head_gradient=float(zero.cost_critic.weight.grad.norm())
    assert head_gradient>0 and float(zero.cost_critic.bias.grad.abs())>0
    trainer.value_optimizer.step()
    with torch.no_grad():positive_loss=float((zero(*observation)['cost_value']-1).square().mean())
    assert positive_loss<float(loss.detach()) and bool((zero.cost_critic.weight!=0).any())
    # Saved nonzero trained cost weights must survive evaluation construction/load.
    with tempfile.TemporaryDirectory(dir=str(BASE),prefix='cpu-checkpoints-') as temp:
        paths={}
        configs=[baseline,a,b]
        for variant,contract,settings in zip(('baseline',*VARIANTS),contracts,configs):
            if variant==VARIANTS[1]:source=trainer
            else:
                policy=ShortPolicy(contract=contract,size='large') if variant=='baseline' else policy_type(variant,fresh=True)(contract=contract,size='large')
                source=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
            path=Path(temp)/(variant+'.pt');torch.save(payload(source,settings),path);paths[variant]=path
            if variant!=VARIANTS[1]:del source,policy
        accepted=[];rejected=[]
        for variant,contract,settings in zip(('baseline',*VARIANTS),contracts,configs):
            policy=ShortPolicy(contract=contract,size='large') if variant=='baseline' else policy_type(variant,fresh=False)(contract=contract,size='large')
            target=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
            target.load(paths[variant]);accepted.append(variant)
            if variant==VARIANTS[1]:
                assert torch.equal(policy.cost_critic.weight,zero.cost_critic.weight)
                assert bool((policy.cost_critic.weight!=0).any())
            for other,path in paths.items():
                if other==variant:continue
                try:target.load(path)
                except ValueError as error:
                    assert 'mismatch' in str(error);rejected.append([variant,other])
                else:raise AssertionError('Cross-variant strict load accepted')
            del target,policy
    # Static dry-run proof: the no-execute branch returns before process creation.
    tree=ast.parse((BASE/'support/run_ablation.py').read_text())
    branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.UnaryOp)
        and isinstance(n.test.op,ast.Not) and isinstance(n.test.operand,ast.Attribute)
        and isinstance(n.test.operand.value,ast.Name) and n.test.operand.value.id=='args'
        and n.test.operand.attr=='execute')
    assert isinstance(branch.body[-1],ast.Return)
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('Popen','run_child') for n in ast.walk(branch))
    changed_inputs=[p for p,h in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    assert not changed_inputs
    result=dict(completed=True,GPU_used=False,actual_model_size='large',A_settings_diff=diff_a,B_settings_diff=diff_b,
        exact_gamma=LONG_GAMMA,PBRS_gamma_matches_actual_environment=True,
        A_initial_model_tensors_and_RNG_unchanged=True,
        B_changed_state_tensors_only=changed,actor_rewardcritic_valueencoder_std_identical=True,RNG_identical=True,
        evaluation_constructor_not_zeroed=True,zero_cost_prediction_after_reward_encoder_update=True,zero_cost_GAE_zero=True,
        positive_cost_head_gradient_norm=head_gradient,positive_cost_loss_before=float(loss.detach()),positive_cost_loss_after=positive_loss,
        same_variant_strict_load_accepted=accepted,cross_variant_strict_load_rejected=rejected,
        trained_nonzero_cost_head_preserved_on_evaluation_load=True,dry_run_returns_before_process_execution=True,
        active_source_unchanged=True,changed_inputs=changed_inputs,
        original_teacher_evidence_and_reference_accepted_for_baseline_A_B=reference_checks,
        thumb_support_schema=patch['contract']['schema'],diagnostic_schema=DIAGNOSTIC_CONTRACT['schema'],
        corrected_rear_plane=patch['plane'].tolist(),
        scope='CPU initialization/algebra/strict identity only; corrected thumb v3 geometry, no native training result')
    (BASE/'cpu_self_test.json').write_text(json.dumps(result,indent=2)+'\n')
    (BASE/'cpu_inputs.json').write_text(json.dumps(pins,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
