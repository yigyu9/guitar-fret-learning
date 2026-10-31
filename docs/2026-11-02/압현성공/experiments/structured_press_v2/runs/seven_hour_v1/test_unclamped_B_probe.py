"""B16 마스크·단일 native 실행·원본 이력/관측·strict 이후 적용의 CPU 검사."""
from pathlib import Path
from types import SimpleNamespace
import copy
import json
import tempfile
from unittest.mock import patch
import unittest
import torch
import unclamped_B_probe as probe


class UnclampedTests(unittest.TestCase):
    def fake(self):
        class Native:
            def step(self,actions):
                self.calls+=1;self.sent=actions.clone();self.controller.target.copy_(actions*.5)
                self.environment.native_clock+=1
                return ('old-observation',2,3,4,5,6)
        class Pool(Native):
            def step(self,actions):return 'original-supported-step'
        class BaseTrainer:
            def load(self,*args):return 'strict-loaded'
        class Trainer(BaseTrainer):pass
        pool=Pool();pool.calls=0;pool.structured=dict(stage='B',active_axes=list(range(12))+list(range(29,33)))
        env=SimpleNamespace(hold_action=torch.full((1,39),.1),action_min=torch.full((1,39),float('inf')),
            action_max=torch.full((1,39),float('-inf')),last_applied_action=torch.zeros(1,39),
            native_clock=0,motion_phase=torch.tensor([2]))
        env.hold_action[:,33:]=0
        env.observation=lambda:dict(last=env.last_applied_action.clone(),clock=env.native_clock)
        pool.environment=env;pool.controller=SimpleNamespace(target=torch.zeros(1,39),active=torch.arange(39),
            reference=torch.zeros(39),action_low=-torch.ones(39),action_high=torch.ones(39))
        sp=SimpleNamespace(StructuredPool=Pool,StructuredTrainer=Trainer,
            normalized_action=lambda target,*args:target)
        official=SimpleNamespace(_pins=lambda settings,out,extra=():extra)
        trainer=Trainer();trainer.updates=9;trainer.policy=torch.nn.Linear(1,1)
        return sp,official,pool,trainer

    def test_mask_native_history_and_phase_preserved(self):
        sp,o,p,t=self.fake();config=copy.deepcopy(p.structured);actions=torch.full((1,39),.9)
        result=probe.unclamped_step(p,actions,sp)
        self.assertEqual(p.calls,1);self.assertEqual(p.environment.native_clock,1)
        self.assertEqual(p.structured,config);self.assertEqual(p.environment.motion_phase.item(),2)
        self.assertTrue(torch.equal(p.sent[0,:12],actions[0,:12]))
        self.assertTrue(torch.equal(p.sent[0,12:29],p.environment.hold_action[0,12:29]))
        self.assertTrue(torch.equal(p.sent[0,33:],torch.zeros(6)))
        self.assertTrue(torch.equal(p.environment.action_min,p.sent));self.assertTrue(torch.equal(p.environment.action_max,p.sent))
        self.assertTrue(torch.equal(p.environment.last_applied_action,p.controller.target))
        self.assertTrue(torch.equal(result[0]['last'],p.controller.target));self.assertEqual(result[1:],(2,3,4,5,6))
        self.assertTrue(torch.equal(actions,torch.full((1,39),.9)))

    def test_strict_arm_restore_and_pin(self):
        sp,o,p,t=self.fake();step=sp.StructuredPool.step;pins=o._pins
        with self.assertRaisesRegex(RuntimeError,'test'):
            with probe.execution_context(sp,o) as record:
                self.assertEqual(p.step(torch.ones(1,39)),'original-supported-step');self.assertEqual(p.calls,0)
                self.assertEqual(t.load('source'),'strict-loaded');self.assertTrue(record['armed'])
                p.step(torch.ones(1,39));self.assertEqual(p.calls,1)
                self.assertIn(Path(probe.__file__).resolve(),o._pins({},Path('/tmp')))
                raise RuntimeError('test')
        self.assertIs(sp.StructuredPool.step,step);self.assertIs(o._pins,pins)
        self.assertNotIn('load',sp.StructuredTrainer.__dict__)
        with probe.execution_context(sp,o):pass
        self.assertIs(sp.StructuredPool.step,step)

    def test_report_checkpoint_sha_contract_preserved(self):
        from guitar_learning.tool.experiments import structured_press as real_sp
        from guitar_learning.training import finger_skill_runner as real_official
        sp,o,p,t=self.fake()
        with tempfile.TemporaryDirectory() as directory:
            checkpoint=Path(directory)/'source.pt';out=Path(directory)/'out'
            config=dict(stage='B',finger='pinky',active_axes=p.structured['active_axes'])
            torch.save(dict(metadata=dict(settings=dict(structured_press=config)),
                model=t.policy.state_dict(),updates=t.updates),checkpoint)
            digest=probe.fixed.digest(checkpoint)
            def native(*args):
                t.load(checkpoint);out.mkdir()
                report=dict(completed=True,lifecycle_verified=True,original_strict_load_completed=True,
                    source_sha256=digest,checkpoint_sha256=digest,limitations=['original'])
                (out/'report.json').write_text(json.dumps(report));return report
            with patch.object(real_sp,'StructuredPool',sp.StructuredPool), \
                    patch.object(real_sp,'StructuredTrainer',sp.StructuredTrainer), \
                    patch.object(real_official,'_pins',o._pins),patch.object(probe.fixed,'run',native):
                report=probe.run(checkpoint,out)
            self.assertEqual(report['source_sha256'],digest)
            self.assertEqual(report['source_sha256'],report['checkpoint_sha256'])
            self.assertIsInstance(report['source_sha256'],str)
            self.assertEqual(report['execution_input_sha256'][str(Path(probe.__file__).resolve())],
                probe.fixed.digest(Path(probe.__file__).resolve()))


    def test_first_policy_import_is_inside_path_context(self):
        from contextlib import contextmanager
        from unittest.mock import patch
        import builtins
        events=[];active=[False]
        @contextmanager
        def paths():
            active[0]=True;events.append('enter')
            try:yield
            finally:active[0]=False;events.append('exit')
        original_import=builtins.__import__
        def importing(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='guitar_learning.tool.experiments.structured_geometry':
                return SimpleNamespace(nested_input_paths=paths)
            if name=='guitar_learning.tool.experiments' and 'structured_press' in fromlist:
                self.assertTrue(active[0]);events.append('policy_import')
                return SimpleNamespace(structured_press=object())
            return original_import(name,globals,locals,fromlist,level)
        def body(*args):
            from guitar_learning.tool.experiments import structured_press
            raise RuntimeError('body failure')
        with patch.object(builtins,'__import__',side_effect=importing),patch.object(probe,'_run',side_effect=body):
            with self.assertRaisesRegex(RuntimeError,'body failure'):
                probe.run(Path('/tmp/source.pt'),Path('/tmp/new_probe_output'))
        self.assertEqual(events,['enter','policy_import','exit'])
        self.assertFalse(active[0])


if __name__=='__main__':unittest.main()
