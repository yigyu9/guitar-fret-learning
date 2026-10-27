"""Contract migration must preserve actors and never bypass strict resume."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import torch
from guitar_learning.specialist_policy import SpecialistPolicy
from guitar_learning.ppo import PPOTrainer
from guitar_learning.musical_quality import HISTORY_FIELDS, metadata, history_scales, preparation_metadata
from guitar_learning.musical_quality_transfer import apply_actor_initialization

ROOT = Path(__file__).resolve().parents[2]
RESET = ROOT/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_actionable_preparation_v1/left_ppo_eval_v1/reset_00.json'


def contracts():
    old = json.loads(RESET.read_text())['training_contract']
    new = copy.deepcopy(old); obs = new['observation']
    obs['dimension'] += len(HISTORY_FIELDS)
    obs['fields'] += ['quality_history.'+name for name in HISTORY_FIELDS]
    obs['scales'] += history_scales()
    obs['musical_quality_history'] = dict(fields=list(HISTORY_FIELDS), base_dimension=536)
    for section in ('task', 'reward'): new[section]['musical_quality'] = metadata()
    new['reward']['actionable_preparation'] = preparation_metadata()
    return old,new


class TransferTests(unittest.TestCase):
    def test_actor_equivalence_and_fresh_values_then_strict_resume(self):
        torch.set_num_threads(1)
        for role in ('left', 'right'):
            with tempfile.TemporaryDirectory() as folder:
                old,new = contracts()
                old['task']['specialist']['role'] = new['task']['specialist']['role'] = role
                source = SpecialistPolicy(536, contract=old, role=role)
                # Nonzero heads make an incorrect encoder transfer observable.
                with torch.no_grad(): source.actor_heads[role].weight.normal_(0, .01)
                trainer = PPOTrainer(source); trainer.updates=1
                path=Path(folder)/'source.pt'; trainer.save(path)
                target = SpecialistPolicy(536+len(HISTORY_FIELDS), contract=new, role=role)
                value_before={k:v.clone() for k,v in target.state_dict().items() if k.startswith(('value_encoder.', 'reward_critic.', 'cost_critic.'))}
                report=apply_actor_initialization(target,path,kind='ppo')
                self.assertEqual(report['source_state_dim'],536)
                source.eval();target.eval()
                state=torch.randn(2,536); extras=torch.randn(2,len(HISTORY_FIELDS))
                events=torch.randn(2,64,24);mask=torch.ones(2,64,dtype=torch.bool)
                priority=torch.randn(2,2,24);pm=torch.ones(2,2,dtype=torch.bool)
                with torch.no_grad():
                    a=source(state,events,mask,priority,pm)['mean']
                    b=target(torch.cat((state,extras),-1),events,mask,priority,pm)['mean']
                torch.testing.assert_close(a,b,rtol=1e-5,atol=1e-7)
                first='actor_encoders.'+role+'.state.0.weight'
                torch.testing.assert_close(target.state_dict()[first][:,:536],source.state_dict()[first],rtol=0,atol=0)
                self.assertEqual(torch.count_nonzero(target.state_dict()[first][:,536:]).item(),0)
                for k,v in value_before.items():torch.testing.assert_close(target.state_dict()[k],v,rtol=0,atol=0)
                fresh=PPOTrainer(target)
                self.assertEqual(fresh.updates,0)
                with self.assertRaises(ValueError): fresh.load(path)
                migrated=Path(folder)/'quality.pt';fresh.save(migrated)
                restored=PPOTrainer(SpecialistPolicy(536+len(HISTORY_FIELDS),contract=new,role=role))
                restored.load(migrated)
                self.assertEqual(restored.updates,0)

    def test_mismatched_physics_or_base_inputs_rejected_before_mutation(self):
        old,new=contracts()
        with tempfile.TemporaryDirectory() as folder:
            source=SpecialistPolicy(536,contract=old,role='left');trainer=PPOTrainer(source);trainer.updates=1
            path=Path(folder)/'source.pt';trainer.save(path)
            for section, key, value in [('termination','guitar_position_failure_m',999),('observation','clip_abs',999),('task','duration_s',999)]:
                altered=copy.deepcopy(new);altered[section][key]=value
                target=SpecialistPolicy(536+len(HISTORY_FIELDS),contract=altered,role='left')
                before={k:v.clone() for k,v in target.state_dict().items()}
                with self.assertRaises(ValueError):apply_actor_initialization(target,path,kind='ppo')
                for k,v in before.items():torch.testing.assert_close(target.state_dict()[k],v,rtol=0,atol=0)


    def test_quality_tail_scale_dimension_and_order_are_checked(self):
        old,new=contracts()
        with tempfile.TemporaryDirectory() as folder:
            source=SpecialistPolicy(536,contract=old,role='left');trainer=PPOTrainer(source);trainer.updates=1
            path=Path(folder)/'source.pt';trainer.save(path)
            for mutation in ('scale','missing_scale','dimension','field'):
                altered=copy.deepcopy(new);obs=altered['observation']
                if mutation=='scale':obs['scales'][-1]=999
                elif mutation=='missing_scale':obs['scales'].pop()
                elif mutation=='dimension':obs['dimension']-=1
                else:obs['fields'][-1]='wrong_field'
                target=SpecialistPolicy(536+len(HISTORY_FIELDS),contract=altered,role='left')
                with self.assertRaises(ValueError):apply_actor_initialization(target,path,kind='ppo')


if __name__ == '__main__':unittest.main()
