import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
from guitar_learning import imitation_io, musical_quality_environment, recording
from guitar_learning.local_skills import probe, controls
from guitar_learning.specialist_policy import SpecialistPolicy


class ProbeTests(unittest.TestCase):
    def test_gate_requires_whole_safe_quality_episode(self):
        good = dict(valid=True, reason='timeline_complete', task_time_s=7.,
                    musical_quality=dict(stage_success=True))
        self.assertTrue(probe.successful_episode(good,ticks=420))
        self.assertFalse(probe.successful_episode(good,ticks=419))
        for key,value in (('valid',False),('reason','terminal_failure'),('task_time_s',6.9),('musical_quality',{})):
            self.assertFalse(probe.successful_episode(dict(good,**{key:value}),ticks=420))

    def test_capture_contains_pre_action_observation_and_preserves_failure(self):
        torch.set_num_threads(1)
        contract = dict(schema='guitar_learning.training.v1', observation={}, action={}, task={}, reward={}, termination={})
        model = SpecialistPolicy(563, size='small', role='left', contract=contract)
        class Env:
            def __init__(self):
                self.contract = copy.deepcopy(contract)
                self.task = SimpleNamespace(targets=[SimpleNamespace(end_s=4.3522)])
                props = np.zeros(1)
                self.scene = SimpleNamespace(human_root_fixed=True,guitar_root_fixed=False,
                    guitar_gravity_disabled=False, forbidden_calls=[],pd_properties=props)
                self.control = SimpleNamespace(session=SimpleNamespace(scene=self.scene), original_properties=props.copy(),
                    codec_previous=np.zeros(81),contract=SimpleNamespace(active_indices=np.arange(39),
                        q_ref=np.zeros(81),action_lower=-np.ones(39),action_upper=np.ones(39)))
            def obs(self):
                state=np.zeros(563,dtype=np.float32);state[0]=self.ticks/60.
                return dict(state=state,events=np.zeros((64,24),dtype=np.float32),mask=np.zeros(64,dtype=bool),
                    priority_events=np.zeros((2,24),dtype=np.float32),priority_mask=np.zeros(2,dtype=bool))
            def reset(self):
                self.ticks=0
                return self.obs(),dict(training_contract=self.contract,musical_quality={})
            def step(self,action):
                self.ticks+=1;done=self.ticks==420
                info=dict(musical_quality={},failure_reasons=[])
                if done:info['episode']=dict(valid=True,reason='timeline_complete',task_time_s=7.,
                    musical_quality=dict(stage_success=False))
                return self.obs(),0.,done,False,info
            def close(self):pass
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);checkpoint=root/'model.pt';settings=root/'settings.json';settings.write_text('{}')
            torch.save(dict(identity=dict(schema='guitar_learning_ppo_v1',architecture=model.architecture),
                            updates=1,model=model.state_dict()),checkpoint)
            args=SimpleNamespace(out=root/'out',checkpoint=checkpoint,settings=settings,device='cpu',candidates=['policy'])
            env=Env()
            with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}), \
                    patch.object(musical_quality_environment,'build_environment',return_value=env), \
                    patch.object(imitation_io,'pin_inputs',return_value={str(checkpoint):recording.digest(checkpoint)}), \
                    patch.object(recording,'project_source_paths',return_value=set()), \
                    patch.object(probe,'available_gib',return_value=32.),contextlib.redirect_stdout(io.StringIO()):
                result=probe.run(dict(specialist=dict(role='left'),seed=7,timing=dict(stage_index=1,pre_roll_s=3.)),args)
            self.assertFalse(result[0]['success'])
            self.assertTrue(result[0]['completed'])
            with np.load(args.out/'policy/demonstration.npz',allow_pickle=False) as values:
                self.assertEqual(values['state'].shape,(420,563))
                self.assertEqual(values['mask'].dtype,np.bool_)
                self.assertEqual(float(values['state'][0,0]),0.)
                self.assertAlmostEqual(float(values['state'][-1,0]),419/60.,places=5)
                self.assertFalse(values['intervention'].any())
                self.assertTrue((values['action'][:,33:]==0).all())
            self.assertEqual(json.loads((args.out/'result.json').read_text())['successful_candidates'],[])
            args.out = root/'cleanup_failure'
            original_step = env.step
            def successful_step(action):
                observation,reward,terminated,truncated,info = original_step(action)
                if terminated: info['episode']['musical_quality']['stage_success'] = True
                return observation,reward,terminated,truncated,info
            with patch.dict(sys.modules,{'isaacgym':SimpleNamespace()}), \
                    patch.object(musical_quality_environment,'build_environment',return_value=env), \
                    patch.object(imitation_io,'pin_inputs',return_value={str(checkpoint):recording.digest(checkpoint)}), \
                    patch.object(recording,'project_source_paths',return_value=set()), \
                    patch.object(probe,'available_gib',return_value=32.), \
                    patch.object(env,'step',side_effect=successful_step), \
                    patch.object(env,'close',side_effect=OSError('native close failed')), \
                    contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(RuntimeError,'cleanup failed'):
                    probe.run(dict(specialist=dict(role='left'),seed=7,timing=dict(stage_index=1,pre_roll_s=3.)),args)
            overall=json.loads((args.out/'result.json').read_text())
            self.assertEqual(overall['cleanup_error']['type'],'OSError')
            self.assertEqual(overall['successful_candidates'],[])
            case=json.loads((args.out/'policy/result.json').read_text())
            self.assertFalse(case['success'])
            self.assertEqual(case['cleanup_error']['type'],'OSError')


if __name__=='__main__':unittest.main()
