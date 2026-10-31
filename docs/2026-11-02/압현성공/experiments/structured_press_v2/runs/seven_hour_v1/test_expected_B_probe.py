"""B16 분포·inactive23·strict 위임·초기경로·출력표기를 CPU에서 검사한다."""
from contextlib import contextmanager
import builtins
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
import torch
import expected_B_probe as p


class BExpectedTests(unittest.TestCase):
    def fake(self):
        axes=list(range(12))+list(range(29,33))
        class Policy(torch.nn.Module):
            phase='J'
            def __init__(self):super().__init__();self.weight=torch.nn.Parameter(torch.ones(1))
            def _active_mask(self):return torch.tensor([i in axes for i in range(39)])
            def act(self,*args,deterministic=False):
                mean=torch.linspace(-10,10,78).reshape(2,39)
                result=dict(mean=mean,log_std=torch.full_like(mean,-3.),latent=mean,action=mean.tanh())
                result['logp']=self.log_probability(mean,result['log_std'],mean);return result
            def log_probability(self,mean,std,latent):return latent[...,self._active_mask()].square().sum(-1)
        class Trainer:
            def __init__(self):self.policy=Policy();self.updates=9
            def load(self,*args):self.loaded=True;return {'strict':'original_load'}
        return axes,Policy,Trainer

    def test_active16_inactive23_point_and_context_restore(self):
        axes,Policy,Trainer=self.fake();official=SimpleNamespace(_DeterministicPolicy=object(),_pins=lambda *args:[])
        sp=SimpleNamespace(StructuredTrainer=Trainer);before=official._DeterministicPolicy,official._pins,Trainer.load
        for mode in p.MODES:
            policy=Policy();original=policy.act();trainer=Trainer()
            with p.execution_context(sp,official,axes,torch.ones(39)*2,torch.ones(39),mode) as record:
                self.assertEqual(trainer.load('source'),{'strict':'original_load'})
                result=official._DeterministicPolicy(policy).act();active=policy._active_mask()
                self.assertTrue(torch.equal(result['mean'],original['mean']));self.assertTrue(torch.equal(result['log_std'],original['log_std']))
                self.assertTrue(torch.equal(result['action'][:,~active],original['action'][:,~active]))
                self.assertTrue(torch.equal(result['latent'][:,~active],original['latent'][:,~active]))
                self.assertTrue(torch.equal(result['action'][:,active],result['latent'][:,active].tanh()))
                self.assertTrue(torch.equal(result['logp'],policy.log_probability(result['mean'],result['log_std'],result['latent'])))
                if mode=='latent_mean':
                    for key in original:self.assertTrue(torch.equal(result[key],original[key]))
                self.assertEqual(record['inactive_exact_calls'],1)
            self.assertEqual(before,(official._DeterministicPolicy,official._pins,Trainer.load))
        with self.assertRaises(RuntimeError):
            with p.execution_context(sp,official,axes,torch.ones(39),torch.ones(39),'requested_angle_mean'):raise RuntimeError('cleanup')
        self.assertEqual(before,(official._DeterministicPolicy,official._pins,Trainer.load))

    def test_actual_pinky_B_codec_and_free_rejection(self):
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.tool.experiments import structured_press as sp
            source=p.fixed.ROOT/'pinky_B_seed7_v1/100/train/J/final.pt'
            before=p.fixed.digest(source);payload=torch.load(source,map_location='cpu',weights_only=False)
            config,positive,negative,catalog=p.codec(payload,sp)
            self.assertEqual(config['stage'],'B');self.assertEqual(config['active_axes'],list(range(12))+list(range(29,33)))
            self.assertTrue((positive>0).all() and (negative>0).all());self.assertEqual(p.fixed.digest(source),before)
            payload['metadata']['settings']['structured_press']['stage']='free_v9'
            with self.assertRaisesRegex(ValueError,'B16'):p.codec(payload,sp)

    def test_original_strict_load_source_preserved_and_mode_tags(self):
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.tool.experiments import structured_press as sp
            from guitar_learning.training import finger_skill_runner as official
            axes,Policy,Trainer=self.fake();config=dict(stage='B',finger='pinky',active_axes=axes)
            with tempfile.TemporaryDirectory() as tmp:
                cp=Path(tmp)/'source.pt';out=Path(tmp)/'out';catalog=Path(tmp)/'catalog.json';catalog.write_text('{}')
                payload=dict(metadata=dict(settings=dict(structured_press=config,ppo=dict(gamma=.99,cost_gamma=1.))),model=Policy().state_dict(),updates=9)
                torch.save(payload,cp);source_sha=p.fixed.digest(cp)
                def native(*args):
                    trainer=sp.StructuredTrainer();trainer.load(cp)
                    official._DeterministicPolicy(trainer.policy).act()
                    out.mkdir();report=dict(completed=True,lifecycle_verified=True,original_strict_load_completed=True,
                        checkpoint_sha256=source_sha,initial_conditions={'count':32},first_episode_per_env=True,failed_episodes_in_denominator=True)
                    (out/'report.json').write_text(json.dumps(report));return report
                with patch.object(sp,'StructuredTrainer',Trainer),patch.object(p,'codec',return_value=(config,torch.ones(39),torch.ones(39),catalog)), \
                    patch.object(official,'_validate_metadata_schema'),patch.object(official,'_validate_pins'),patch.object(p.fixed,'run',side_effect=native), \
                    patch.object(p,'raw_metrics',return_value={'count':32,'scope':'undiscounted'}):
                    report=p.run(cp,out)
                self.assertEqual(report['optimizer_updates_difference'],0);self.assertTrue(report['stage_B_support_unchanged'])
                self.assertFalse(report['deterministic_policy_unchanged']);self.assertTrue(report['clamp_unchanged'])
                self.assertEqual(report['initial_conditions']['count'],32);self.assertEqual(p.fixed.digest(cp),source_sha)
                self.assertEqual(report['execution_audit']['act_calls'],report['execution_audit']['inactive_exact_calls'])

    def test_outer_paths_before_policy_import(self):
        active=[False];events=[]
        @contextmanager
        def paths():
            active[0]=True;events.append('enter')
            try:yield
            finally:active[0]=False;events.append('exit')
        original=builtins.__import__
        def importing(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='guitar_learning.tool.experiments.structured_geometry':return SimpleNamespace(nested_input_paths=paths)
            if name=='guitar_learning.tool.experiments' and 'structured_press' in fromlist:
                self.assertTrue(active[0]);events.append('policy');return SimpleNamespace(structured_press=object())
            return original(name,globals,locals,fromlist,level)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(builtins,'__import__',side_effect=importing),patch.object(torch,'load',side_effect=RuntimeError('before physics')):
                with self.assertRaises(RuntimeError):p.run(Path(tmp)/'cp',Path(tmp)/'new')
        self.assertEqual(events,['enter','policy','exit'])


if __name__=='__main__':unittest.main()
