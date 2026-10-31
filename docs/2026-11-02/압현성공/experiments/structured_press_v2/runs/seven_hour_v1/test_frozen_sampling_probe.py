"""분포 보존·복원·핀·stochastic 표기/SHA 갱신의 CPU 검사."""
from pathlib import Path
from types import SimpleNamespace
import json
import tempfile
import unittest
import frozen_sampling_probe as probe


class FrozenTests(unittest.TestCase):
    def test_sampling_and_restore(self):
        class Policy:
            phase='J';active_mask=[True]*33
            def forward(self,*args):return dict(mean=mean,log_std=std)
            def __call__(self,*args):return self.forward(*args)
            def act(self,*args,deterministic=True):return deterministic
        mean=object();std=object();original_forward=Policy.forward
        original_pins=lambda settings,out,extra=():extra
        original_wrapper=object();official=SimpleNamespace(_pins=original_pins,_DeterministicPolicy=original_wrapper)
        sp=SimpleNamespace(StructuredPolicy=Policy)
        with self.assertRaisesRegex(RuntimeError,'test'):
            with probe.sampling_context(sp,official):
                policy=Policy();result=policy.forward()
                self.assertIs(result['mean'],mean);self.assertIs(result['log_std'],std)
                wrapped=official._DeterministicPolicy(policy)
                self.assertFalse(wrapped.act('observation'));self.assertIs(wrapped()['mean'],mean)
                pins=official._pins({},Path('/tmp'),[])
                self.assertIn(Path(probe.__file__).resolve(),pins)
                self.assertTrue(any(p.name=='noise_probe.py' for p in pins))
                raise RuntimeError('test')
        self.assertIs(Policy.forward,original_forward);self.assertIs(official._pins,original_pins)
        self.assertIs(official._DeterministicPolicy,original_wrapper)

    def test_annotations_and_original_pin(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'native').mkdir();native=out/'native/report.json'
            native.write_text(json.dumps(dict(completed=True,lifecycle_verified=True)))
            original=probe.trace.digest(native);source=out/'source';source.write_text('immutable')
            before={str(source):probe.trace.digest(source)}
            (out/'summary.json').write_text(json.dumps(dict(completed=True,output_sha256={str(native):original})))
            probe.annotate(out,before)
            summary=json.loads((out/'summary.json').read_text());report=json.loads(native.read_text())
            self.assertTrue(summary['completed']);self.assertEqual(summary['policy_mode'],'stochastic_frozen_checkpoint')
            self.assertEqual(report['original_native_report_sha256'],original)
            self.assertEqual(summary['output_sha256'][str(native)],probe.trace.digest(native))
            self.assertIn('평균 정책 평가가 아니다',(out/'SUMMARY.md').read_text())
            source.write_text('changed')
            with self.assertRaisesRegex(ValueError,'changed'):probe.annotate(out,before)
            self.assertFalse(json.loads((out/'summary.json').read_text())['completed'])


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
