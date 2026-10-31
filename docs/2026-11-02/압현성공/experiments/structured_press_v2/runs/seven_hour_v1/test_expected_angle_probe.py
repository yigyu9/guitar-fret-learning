"""GH 정확도·piecewise 기댓값·원래 정책/비활성축 보존을 CPU에서 검사한다."""
from contextlib import contextmanager
import builtins
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import patch
import numpy as np
import torch
import expected_angle_probe as p


class ExpectedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):torch.set_num_threads(1)

    def test_zero_sigma_symmetric_span_and_zero_mean_integral(self):
        mean=torch.linspace(-8,8,33,dtype=torch.float64);zero=torch.zeros_like(mean)
        a,b=p.moments(mean,zero)
        self.assertTrue(torch.allclose(a,mean.tanh(),atol=1e-14,rtol=0))
        self.assertTrue(torch.allclose(b,mean.tanh().abs(),atol=1e-14,rtol=0))
        sigma=torch.full_like(mean,.15);span=torch.ones_like(mean)
        action=p.deployment_action(mean,sigma.log(),span,span,'requested_angle_mean')
        expected,_=p.moments(mean,sigma)
        self.assertTrue(torch.allclose(action,expected,atol=1e-14,rtol=0))
        m=torch.tensor([0.],dtype=torch.float64);s=torch.tensor([.15],dtype=torch.float64)
        t,absolute=p.moments(m,s)
        grid=np.linspace(0,10,100001)
        independent=2*np.trapz(np.tanh(.15*grid)*np.exp(-grid**2/2)/np.sqrt(2*np.pi),grid)
        self.assertLess(abs(t.item()),1e-14);self.assertLess(abs(absolute.item()-independent),2e-7)
        # μ0의 비대칭 span은 큰 쪽으로 양의 요청각 drift를 만든다.
        action=p.deployment_action(m,s.log(),torch.tensor([2.]),torch.tensor([1.]),'requested_angle_mean')
        self.assertAlmostEqual(action.item(),absolute.item()/4,places=12)

    def test_64_128_and_monte_carlo_across_actual_sigma_and_means(self):
        means=torch.linspace(-8,8,321,dtype=torch.float64)
        for scale in (.049787068367863944,.15):
            sigma=torch.full_like(means,scale);a,b=p.moments(means,sigma,64);c,d=p.moments(means,sigma,128)
            self.assertLess((a-c).abs().max().item(),1e-12)
            self.assertLess((b-d).abs().max().item(),2e-7)
            rng=torch.Generator().manual_seed(4242);noise=torch.randn(300000,generator=rng,dtype=torch.float64)
            for mu in (-8.,-2.,-.15,0.,.15,2.,8.):
                z=mu+scale*noise;action=z.tanh()
                requested=torch.where(action>=0,2*action,.5*action)
                m=torch.tensor([mu],dtype=torch.float64);s=torch.tensor([scale],dtype=torch.float64)
                first,absolute=p.moments(m,s)
                exact=1.25*first+.75*absolute
                tolerance=6*requested.std().item()/len(noise)**.5+2e-6
                self.assertLess(abs(exact.item()-requested.mean().item()),tolerance)

    def test_saved_codec_catalog_and_contract_match(self):
        import sys
        sys.path.insert(0,str(p.trace.STUDY/'runtime'))
        from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
        with nested_input_paths():
            from guitar_learning.tool.experiments import structured_press as sp
            source=p.trace.ROOT/'index_full33_seed7_v1/100/train/J/final.pt'
            payload=torch.load(source,map_location='cpu',weights_only=False)
            a,b,path=p.codec(payload,sp)
            self.assertEqual(a.shape,(39,));self.assertTrue((a>0).all() and (b>0).all())
            self.assertEqual(p.trace.digest(path),payload['metadata']['settings']['structured_press']['geometry_sha256'])

    def test_original_distribution_inactive_logp_baseline_and_restore(self):
        class Policy:
            phase='J'
            def __init__(self):
                self.mean=torch.linspace(-.4,.4,78).reshape(2,39)
                self.std=torch.full((2,39),-.15)
            def _active_mask(self):return torch.arange(39)<33
            def __call__(self,*args):return dict(mean=self.mean,log_std=self.std,reward_value=torch.ones(2),cost_value=torch.zeros(2))
            def log_probability(self,mean,std,latent):return (mean-latent).square().sum(-1)
            def act(self,*args,deterministic=False):return dict(self(),original=deterministic,action=self.mean.tanh(),latent=self.mean,logp=self.log_probability(self.mean,self.std,self.mean))
        old=object();pins=lambda settings,out,extra=():extra
        official=SimpleNamespace(_DeterministicPolicy=old,_pins=pins);policy=Policy()
        for mode in p.MODES:
            with p.deployment_context(official,torch.ones(39)*2,torch.ones(39),mode,goal_axes=range(17,21),arm_axes=range(12)) as impact:
                if mode=='latent_mean':self.assertTrue(official._DeterministicPolicy(policy).act()['original']);continue
                result=official._DeterministicPolicy(policy).act()
                self.assertIs(result['mean'],policy.mean);self.assertIs(result['log_std'],policy.std)
                self.assertTrue(torch.equal(result['action'][:,33:],policy.mean[:,33:].tanh()))
                self.assertTrue(torch.equal(result['latent'][:,33:],policy.mean[:,33:]))
                self.assertTrue(torch.equal(result['logp'],policy.log_probability(policy.mean,policy.std,result['latent'])))
                self.assertTrue(torch.equal(result['action'][:,:33],result['latent'][:,:33].tanh()))
                self.assertIn(Path(p.__file__).resolve(),official._pins({},Path('/tmp')))
            self.assertIs(official._DeterministicPolicy,old);self.assertIs(official._pins,pins)
            self.assertEqual(impact['policy_act_calls'],1)
            self.assertEqual(impact['requested_angle_difference_degrees']['goal4']['count'],8)
            self.assertIsNotNone(impact['requested_angle_difference_degrees']['arm12']['mean_absolute'])
        with self.assertRaises(RuntimeError):
            with p.deployment_context(official,torch.ones(39),torch.ones(39),'requested_angle_mean',goal_axes=range(17,21),arm_axes=range(12)):raise RuntimeError('cleanup')
        self.assertIs(official._DeterministicPolicy,old);self.assertIs(official._pins,pins)

    def test_saturated_active_action_latent_logp_share_exact_point(self):
        class Policy:
            phase='J'
            def __init__(self):self.mean=torch.tensor([[-10.,10.]*20])[:,:39];self.std=torch.full_like(self.mean,-3.)
            def _active_mask(self):return torch.arange(39)<33
            def __call__(self):return dict(mean=self.mean,log_std=self.std)
            def log_probability(self,mean,std,latent):return latent.square().sum(-1)
        old=object();official=SimpleNamespace(_DeterministicPolicy=old,_pins=lambda *args:[])
        policy=Policy()
        for mode in ('normalized_action_mean','requested_angle_mean'):
            with p.deployment_context(official,torch.ones(39),torch.ones(39),mode,goal_axes=range(17,21),arm_axes=range(12)) as impact:
                result=official._DeterministicPolicy(policy).act()
                self.assertTrue(torch.equal(result['action'][:,:33],result['latent'][:,:33].tanh()))
                self.assertTrue(torch.isfinite(result['latent']).all())
                self.assertTrue(torch.equal(result['logp'],policy.log_probability(policy.mean,policy.std,result['latent'])))
                self.assertTrue(torch.equal(result['action'][:,33:],policy.mean[:,33:].tanh()))
                self.assertEqual(impact['finite_latent_adjustment']['saturated_active_count'],33)
                self.assertGreater(impact['finite_latent_adjustment']['max_normalized_action_change'],0.)
            self.assertIs(official._DeterministicPolicy,old)

    def test_first_policy_import_has_outer_paths_and_error_restores(self):
        events=[];active=[False]
        @contextmanager
        def paths():
            active[0]=True;events.append('enter')
            try:yield
            finally:active[0]=False;events.append('exit')
        original=builtins.__import__
        def importing(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='guitar_learning.tool.experiments.structured_geometry':return SimpleNamespace(nested_input_paths=paths)
            if name=='guitar_learning.tool.experiments' and 'structured_press' in fromlist:
                self.assertTrue(active[0]);events.append('policy_import');return SimpleNamespace(structured_press=object())
            if name=='guitar_learning.training' and 'finger_skill_runner' in fromlist:
                return SimpleNamespace(finger_skill_runner=object())
            return original(name,globals,locals,fromlist,level)
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(builtins,'__import__',side_effect=importing),patch.object(torch,'load',side_effect=RuntimeError('stop before physics')):
                with self.assertRaisesRegex(RuntimeError,'stop before physics'):
                    p.run(Path(tmp)/'source.pt',Path(tmp)/'new','requested_angle_mean')
        self.assertEqual(events,['enter','policy_import','exit']);self.assertFalse(active[0])

    def test_annotation_keeps_initial_evidence_and_updates_output_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'native').mkdir();native=out/'native/report.json'
            native.write_text(json.dumps(dict(completed=True,lifecycle_verified=True)))
            initial=out/'initial.npz';initial.write_bytes(b'original first32 q and hold evidence')
            source=out/'source.pt';source.write_bytes(b'unchanged checkpoint')
            before={str(source):p.trace.digest(source)}
            original=p.trace.digest(native);initial_sha=p.trace.digest(initial)
            (out/'summary.json').write_text(json.dumps(dict(completed=True,output_sha256={str(native):original,str(initial):initial_sha})))
            p.annotate(out,before,'requested_angle_mean',{'policy_act_calls':1})
            report=json.loads((out/'summary.json').read_text())
            self.assertTrue(report['completed']);self.assertEqual(report['observed_request_impact']['policy_act_calls'],1)
            self.assertEqual(report['output_sha256'][str(native)],p.trace.digest(native))
            self.assertEqual(report['output_sha256'][str(initial)],initial_sha)
            self.assertEqual(report['optimizer_updates_difference'],0)
            source.write_bytes(b'changed')
            with self.assertRaises(ValueError):p.annotate(out,before,'requested_angle_mean',None)
            self.assertFalse(json.loads((out/'summary.json').read_text())['completed'])

    def test_invalid_inputs_rejected(self):
        with self.assertRaises(ValueError):p.moments(torch.zeros(1),torch.tensor([-1.]))
        with self.assertRaises(ValueError):p.deployment_action(torch.zeros(1),torch.zeros(1),torch.zeros(1),torch.ones(1),'requested_angle_mean')
        with self.assertRaises(ValueError):p.run(Path('/tmp/missing'),Path('/tmp/new'),'invalid')


if __name__=='__main__':unittest.main()
