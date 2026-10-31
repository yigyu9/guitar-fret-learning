"""그룹 선택과 원본 draw/RNG·유한 밀도·factory 복구의 CPU 회귀 검사."""
from pathlib import Path
import ast
from types import SimpleNamespace
import unittest
import tempfile
import hashlib
import torch
import group_sampling_probe as g


class Policy:
    phase='J'
    def __init__(self):self.mean=torch.linspace(-.7,.7,39).repeat(8,1);self.std=torch.full_like(self.mean,-3.);self.calls=0
    def _active_mask(self):return torch.arange(39)<33
    def log_probability(self,mean,std,latent):return torch.distributions.Normal(mean[...,:33],std[...,:33].exp()).log_prob(latent[...,:33]).sum(-1)
    def act(self,*inputs,deterministic=False):
        self.calls+=1;latent=self.mean.clone();noise=torch.zeros_like(latent)
        noise[...,:33]=torch.distributions.Normal(torch.zeros_like(latent[...,:33]),self.std[...,:33].exp()).sample()
        latent=latent+noise
        return dict(mean=self.mean,log_std=self.std,latent=latent,action=latent.tanh(),logp=self.log_probability(self.mean,self.std,latent))


class Tests(unittest.TestCase):
    def test_existing_output_all_bytes_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)/'completed';(out/'native').mkdir(parents=True)
            for name in ('summary.json','native/report.json','trace.npz','initial.npz','SUMMARY.md'):
                (out/name).write_bytes(b'completed original fixture '+name.encode())
            before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
            with self.assertRaises(FileExistsError):g.run(Path('unused.pt'),out,'all')
            after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}
            self.assertEqual(before,after)

    def test_groups_and_exact_rng_values(self):
        for finger in ('index','middle','ring','pinky'):
            groups=g.groups(dict(finger=finger));self.assertEqual([len(groups[k]) for k in ('goal','arm','other')],[4,12,17])
            for name,selected in groups.items():
                p=Policy();torch.manual_seed(717);native=p.act();rng=torch.get_rng_state().clone();p.calls=0
                torch.manual_seed(717);record=dict(act_calls=0);result=g.GroupPolicy(p,selected,record).act()
                self.assertTrue(torch.equal(torch.get_rng_state(),rng));self.assertEqual(p.calls,1)
                self.assertEqual(record['act_calls'],1)
                self.assertTrue(torch.equal(result['latent'][...,selected],native['latent'][...,selected]))
                rest=[i for i in range(33) if i not in selected]
                self.assertTrue(torch.equal(result['latent'][...,rest],p.mean[...,rest]))
                for key in ('action','latent'):self.assertTrue(torch.equal(result[key][...,33:],native[key][...,33:]))
                for key in ('mean','log_std'):self.assertTrue(torch.equal(result[key],native[key]))
                self.assertTrue(torch.isfinite(result['logp']).all())
                if name=='all':
                    for key in result:self.assertTrue(torch.equal(result[key],native[key]))

    def test_context_restoration(self):
        for error in (False,True):
            factory=lambda p:p;pins=lambda settings,out,extra=():list(extra)
            official=SimpleNamespace(_DeterministicPolicy=factory,_pins=pins)
            try:
                with g.context(official,list(range(33))):
                    self.assertIsInstance(official._DeterministicPolicy(Policy()),g.GroupPolicy)
                    self.assertIn(Path(g.__file__).resolve(),official._pins({},None))
                    if error:raise RuntimeError()
            except RuntimeError:pass
            self.assertIs(official._DeterministicPolicy,factory);self.assertIs(official._pins,pins)

    def test_import_order(self):
        tree=ast.parse(Path(g.__file__).read_text());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
        with_node=next(n for n in run.body if isinstance(n,ast.With))
        self.assertIsInstance(with_node.body[0],ast.Import)
        self.assertEqual(with_node.body[0].names[0].name,'torch')
        before=run.body[:run.body.index(with_node)]
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module.endswith('structured_press') for n in before))


if __name__=='__main__':unittest.main()
