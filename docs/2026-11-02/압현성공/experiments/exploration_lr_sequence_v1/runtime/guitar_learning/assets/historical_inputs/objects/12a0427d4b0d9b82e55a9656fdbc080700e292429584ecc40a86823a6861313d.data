"""Synthetic captures validate BC contracts; no native dynamics are executed."""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest

import numpy as np
import torch

from guitar_learning.tool.experiments.local_skills import learning
from guitar_learning.training.ppo import PPOTrainer
from guitar_learning.tests.quality_fixtures import fixed_note_contract


def capture(root, role='left'):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    contract=fixed_note_contract(root,role)
    architecture=dict(schema='guitar_specialists39_v1')
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    model=SpecialistPolicy(563,role=role,contract=contract)
    trainer=PPOTrainer(model);trainer.updates=1;source=root/'source.pt';trainer.save(source)
    case=root/'teacher';case.mkdir()
    arrays={k:np.zeros((420,)+s,dtype=bool if k in ('mask','priority_mask','intervention') else np.float32)
            for k,s in learning.SHAPES.items()}
    arrays['mask'][:]=True;arrays['priority_mask'][:]=True
    arrays['intervention'][300:]=True;arrays['state'][300:,0]=1.
    arrays['task_time_s']=np.arange(420,dtype=np.float64)/60.
    arrays['action'][300:,0 if role=='left' else 33]=.15
    np.savez_compressed(case/'demonstration.npz',**arrays)
    episode=dict(valid=True,reason='timeline_complete',steps=420,task_time_s=7.,
        timing=dict(safety_invalidated=False,timing_only_stage_success=True,stage_success=True),
        musical_quality=dict(role=role,stage_success=True))
    result=dict(schema=learning.CAPTURE_SCHEMA,role=role,candidate='teacher',completed=True,success=True,
        episode=episode,source_checkpoint=str(source.resolve()),source_checkpoint_sha256=learning.dataset_manifest([source])[str(source.resolve())],
        training_contract_sha256=learning.contract_digest(contract),source_unchanged=True,physical_flags_ok=True,forbidden_calls=[],cleanup_error=None)
    (case/'reset.json').write_text(json.dumps(dict(training_contract=contract)))
    (case/'result.json').write_text(json.dumps(result))
    (root/'result.json').write_text(json.dumps(dict(schema='guitar_learning.local_skill_search.v1',role=role,
        source_unchanged=True,cleanup_error=None,failure=None,successful_candidates=['teacher'],candidates=[result])))
    return case,model,arrays


def fitted(root,role='left',steps=2):
    case,model,_=capture(root,role);data=learning.load_capture(case)
    fit=learning.fit_actor(model,data,steps=steps,batch_size=32)
    path=Path(root)/'bc.pt';learning.save_initialization(model,path,data=data,fit_result=fit)
    return path,data,fit,model


class LocalLearningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_masked_fit_updates_only_selected_actor_preserves_rng_and_reports_both_groups(self):
        for role in ('left','right'):
            with tempfile.TemporaryDirectory() as folder:
                case,model,_=capture(folder,role);data=learning.load_capture(case)
                before={k:v.clone() for k,v in model.state_dict().items()}
                rng=torch.get_rng_state().clone();nrng=np.random.get_state();prng=random.getstate()
                result=learning.fit_actor(model,data,steps=20,batch_size=32)
                self.assertLess(result['final']['local_mse'],result['initial']['local_mse'])
                self.assertEqual((result['local_rows'],result['preservation_rows']),(120,300))
                self.assertIn('prefix_max_abs_error',result['final'])
                self.assertTrue(torch.equal(rng,torch.get_rng_state()))
                self.assertTrue(np.array_equal(nrng[1],np.random.get_state()[1]));self.assertEqual(prng,random.getstate())
                self.assertTrue(result['changed_model_keys'])
                for key,value in model.state_dict().items():
                    if not key.startswith(('actor_encoders.'+role+'.','actor_heads.'+role+'.')):
                        torch.testing.assert_close(value,before[key],rtol=0,atol=0)

    def test_failed_live_or_changed_capture_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            case,_,_=capture(folder);original=json.loads((case/'result.json').read_text())
            for key,value in [('success',False),('source_unchanged',False),('physical_flags_ok',False),
                              ('forbidden_calls',['force']),('cleanup_error',{'error':'close'}),
                              ('source_checkpoint_sha256','wrong')]:
                bad=dict(original,**{key:value});(case/'result.json').write_text(json.dumps(bad))
                with self.assertRaises(ValueError):learning.load_capture(case)
            (case/'result.json').write_text(json.dumps(original))
            (Path(folder)/'result.json').unlink()
            with self.assertRaisesRegex(ValueError,'finalized'):learning.load_capture(case)

    def test_arrays_contract_and_actual_source_policy_are_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            case,_,arrays=capture(folder)
            for key,alter in [('intervention',lambda a:a.fill(False)),('action',lambda a:a.__setitem__((0,33),.1)),
                              ('task_time_s',lambda a:a.__setitem__(1,0.)),('policy_action',lambda a:a.__setitem__((350,0),.2))]:
                damaged={k:v.copy() for k,v in arrays.items()};alter(damaged[key])
                np.savez_compressed(case/'demonstration.npz',**damaged)
                with self.assertRaises(ValueError):learning.load_capture(case)
            np.savez_compressed(case/'demonstration.npz',**arrays)
            reset=json.loads((case/'reset.json').read_text());reset['training_contract']['termination']['failure_cost']=999
            (case/'reset.json').write_text(json.dumps(reset))
            with self.assertRaises(ValueError):learning.load_capture(case)

    def test_bc_artifact_is_actor_only_and_full_identity_remains_strict(self):
        with tempfile.TemporaryDirectory() as folder:
            path,data,fit,source=fitted(folder)
            payload=learning.load_initialization(path)
            self.assertEqual(payload['schema'],learning.SCHEMA)
            self.assertNotIn('identity',payload);self.assertNotIn('updates',payload)
            target=learning.construct(source.architecture);before={k:v.clone() for k,v in target.state_dict().items()}
            rng=torch.get_rng_state().clone()
            learning.apply_actor_initialization(target,path,kind='bc')
            self.assertTrue(torch.equal(rng,torch.get_rng_state()))
            for k,v in target.state_dict().items():
                if k.startswith(('actor_encoders.left.','actor_heads.left.')):
                    torch.testing.assert_close(v,source.state_dict()[k],rtol=0,atol=0)
                elif k=='log_std':torch.testing.assert_close(v[:33],source.log_std[:33],rtol=0,atol=0)
                else:torch.testing.assert_close(v,before[k],rtol=0,atol=0)
            fresh=PPOTrainer(target);self.assertEqual(fresh.updates,0);self.assertFalse(fresh.actor_optimizer.state)
            with self.assertRaises(ValueError):fresh.load(path)
            ppo_path=Path(folder)/'ppo.pt';fresh.save(ppo_path)
            restored=PPOTrainer(learning.construct(target.architecture));restored.load(ppo_path)
            self.assertEqual(restored._identity(),fresh._identity())
            changed=copy.deepcopy(target.architecture);changed['contract']['action']['smoothing_alpha']=.99
            with self.assertRaises(ValueError):learning.apply_actor_initialization(learning.construct(changed),path,kind='bc')
            with self.assertRaises(FileExistsError):learning.save_initialization(source,path,data=data,fit_result=fit)
            (Path(data['capture'])/'demonstration.npz').write_bytes(b'changed')
            with self.assertRaises(RuntimeError):learning.load_initialization(path)


if __name__=='__main__':unittest.main()
