"""새 프레임 생성 없이 배포 factory·argv 복구·native/public SHA 교정을 검사한다."""
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch
import torch
import render_deployment as r


class RenderTests(unittest.TestCase):
    def policy(self):
        class Policy:
            phase='J'
            active_mask=torch.arange(39)<33
            def forward(self,*args):return dict(mean=torch.zeros(2,39),log_std=torch.full((2,39),-3.))
            def __call__(self,*args):return self.forward(*args)
            def _active_mask(self):return self.active_mask
            def act(self,*args,deterministic=False):
                result=self();result.update(deterministic=deterministic,action=result['mean'].tanh(),latent=result['mean'],logp=torch.zeros(2));return result
            def log_probability(self,mean,std,latent):return latent.square().sum(-1)
        return Policy

    def payload(self):
        names=['arm'+str(i) for i in range(12)]+['LH:thumb'+str(i) for i in range(5)]+['LH:index'+str(i) for i in range(4)]+['LH:other'+str(i) for i in range(12)]+['right'+str(i) for i in range(6)]
        return dict(metadata=dict(settings=dict(structured_press=dict(stage='free_v9',finger='index',active_axes=list(range(33))))),
            identity=dict(architecture=dict(contract=dict(action=dict(target_contract=dict(action_order=names))))))

    def test_modes_use_actual_sampling_expected_and_baseline_factories(self):
        import expected_angle_probe as expected
        Policy=self.policy();sp=SimpleNamespace(StructuredPolicy=Policy)
        class Deterministic:
            def __init__(self,policy):self.policy=policy
            def act(self):return self.policy.act(deterministic=True)
        pins=lambda settings,out,extra=():extra
        official=SimpleNamespace(_DeterministicPolicy=Deterministic,_pins=pins)
        for mode in r.MODES:
            with patch.object(expected,'codec',return_value=(torch.ones(39)*2,torch.ones(39),Path('/tmp/catalog'))):
                with r.mode_context(sp,official,self.payload(),mode) as impact:
                    result=official._DeterministicPolicy(Policy()).act()
                    if mode=='stochastic':self.assertFalse(result['deterministic'])
                    elif mode=='latent_mean':self.assertTrue(result['deterministic'])
                    else:self.assertEqual(impact['policy_act_calls'],1);self.assertTrue(torch.isfinite(result['action']).all())
            self.assertIs(official._DeterministicPolicy,Deterministic);self.assertIs(official._pins,pins)
        with self.assertRaises(RuntimeError):
            with r.mode_context(sp,official,self.payload(),'stochastic'):raise RuntimeError('cleanup')
        self.assertIs(official._DeterministicPolicy,Deterministic)

    def fake_output(self,root,checkpoint,label):
        out=root/'renders'/label;out.mkdir(parents=True);public=root/'public';public.mkdir(exist_ok=True)
        report=dict(completed=True,lifecycle_verified=True,training_updates=0,policy_unchanged=True,native_pixels=True,
            source_checkpoint_pins_validated=True,source_pins_unchanged=True,checkpoint_sha256=r.digest(checkpoint))
        (out/'report.json').write_text(json.dumps(report));videos=[]
        for kind in ('hand','fullbody'):
            source=out/(kind+'.mp4');target=public/(label+'_'+kind+'.mp4');source.write_bytes(b'mocked native MP4 fixture');target.write_bytes(source.read_bytes())
            videos.append(dict(kind=kind,path=str(target),sha256=r.digest(source)))
        (out/'publication.json').write_text(json.dumps(dict(checkpoint_sha256=r.digest(checkpoint),videos=videos,image_source='actual deterministic policy',physics_or_policy_modified=False)))
        return out,public

    def test_native_annotation_and_public_sha_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);cp=root/'cp.pt';cp.write_bytes(b'unchanged')
            out,public=self.fake_output(root,cp,'demo');renderer=SimpleNamespace(ROOT=root,PUBLIC=public)
            before={str(cp):r.digest(cp)}
            report,pub=r.annotate(renderer,'demo',cp,'stochastic',before,None)
            self.assertTrue(report['weights_unchanged']);self.assertTrue(report['physics_unchanged']);self.assertTrue(pub['action_rule_changed'])
            self.assertEqual(pub['policy_mode'],'stochastic');self.assertNotIn('actual deterministic policy',pub['image_source'])
            self.assertEqual(pub['deployment_annotation']['original_publication_annotations']['image_source'],'actual deterministic policy')
            self.assertTrue(all(p.suffix=='.mp4' for p in public.iterdir()))
            next(public.iterdir()).write_bytes(b'corrupted')
            with self.assertRaisesRegex(ValueError,'media mismatch'):r.annotate(renderer,'demo',cp,'stochastic',before,None)

    def test_run_normal_argv_restore_and_annotation(self):
        sys.path.insert(0,str(r.ROOT.parents[1]/'runtime'))
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.training import finger_skill_runner as official
            import noise_probe
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);cp=root/'cp.pt';cp.write_bytes(b'fixture')
                argv=sys.argv;pins=official._pins
                def main():self.fake_output(root,cp,'normal')
                renderer=SimpleNamespace(ROOT=root,PUBLIC=root/'public',main=main)
                with patch.object(r,'load_renderer',return_value=renderer),patch.object(noise_probe,'verify_source_seal',return_value='seal'), \
                    patch.object(torch,'load',return_value=self.payload()),patch.object(official,'_validate_metadata_schema'),patch.object(official,'_validate_pins'):
                    report,pub=r.run(cp,'normal','latent_mean')
                self.assertFalse(pub['action_rule_changed']);self.assertEqual(pub['policy_mode'],'latent_mean')
                self.assertIs(sys.argv,argv);self.assertIs(official._pins,pins)

    def test_run_preserves_argv_and_pins_even_on_renderer_error(self):
        sys.path.insert(0,str(r.ROOT.parents[1]/'runtime'))
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.training import finger_skill_runner as official
            import noise_probe
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);cp=root/'cp.pt';cp.write_bytes(b'fixture')
                argv=sys.argv;pins=official._pins
                def main():
                    self.assertIn('--checkpoint',sys.argv)
                    self.assertIsNot(official._pins,pins)
                    raise RuntimeError('render error before frames')
                renderer=SimpleNamespace(ROOT=root,PUBLIC=root/'public',main=main)
                with patch.object(r,'load_renderer',return_value=renderer),patch.object(noise_probe,'verify_source_seal',return_value='seal'), \
                    patch.object(torch,'load',return_value=self.payload()),patch.object(official,'_validate_metadata_schema'),patch.object(official,'_validate_pins'):
                    with self.assertRaisesRegex(RuntimeError,'render error'):r.run(cp,'new','latent_mean')
                self.assertIs(sys.argv,argv);self.assertIs(official._pins,pins)


if __name__=='__main__':unittest.main()
