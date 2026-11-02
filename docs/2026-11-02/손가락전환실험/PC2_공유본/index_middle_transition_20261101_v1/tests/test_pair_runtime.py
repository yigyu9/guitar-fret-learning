import unittest,importlib.util,pathlib,torch
ROOT=next(p for p in pathlib.Path(__file__).resolve().parents if (p/'scripts/tab2body.py').exists());P=ROOT/'docs/2026-11-02/손가락전환실험/도구/runtime.py'
s=importlib.util.spec_from_file_location('pair_runtime',P);rt=importlib.util.module_from_spec(s);s.loader.exec_module(rt)
from guitar_learning.tests.test_gpu_environment import fixture,BUNDLE,SONG
class PairTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):torch.set_num_threads(1)
 def make(self):
  v=rt.build_settings(num_envs=2,size='small');bias=v['natural_press'];cfg=v['transition']
  class E(rt.TransitionEnvironment):
   natural_press=bias;transition=cfg;natural_preparation={'schema':'guitar_learning.natural_preparation.v3','condition':'E4'}
  md,snap=fixture(2);e=E(md,bundle=ROOT/'data/song_bundles'/rt.SONG,song=SONG,skill={'schema':'guitar_learning.finger_skill.v3','phase':'J','scope':'scheduled','hold_ticks':1,'exploration':'independent','planned_transitions':400,'full_song_after':100},hand='left',device='cpu');e.set_evaluation(True,full_song=True);e.reset([0,1],snap);return e,v
 def test_two_finger_policy_permissions_distribution(self):
  e,v=self.make();p=rt.TransitionPolicy(e.observation()['state'].shape[-1],size='small',contract=e.contract,natural_press=v['natural_press'],transition=v['transition']);obs=e.observation();x=[obs[k] for k in ('state','events','mask','priority_events','priority_mask')]
  a=p.act(*x);self.assertEqual(p._active_mask().nonzero().flatten().tolist(),list(range(12))+list(range(17,25)))
  for f in ('index','middle'):self.assertTrue(all(q.requires_grad for q in p.core.finger_heads[f].parameters()))
  for f in ('ring','pinky'):self.assertTrue(all(not q.requires_grad for q in p.core.finger_heads[f].parameters()))
  torch.testing.assert_close(a['log_std'][:,17:25].exp(),torch.full((2,8),.15))
  with torch.no_grad():p.core.finger_log_std[:8].fill_(-5)
  torch.testing.assert_close(p(*x)['log_std'][:,17:25].exp(),torch.full((2,8),.10))
  z=a['latent'].clone();z[:,~p._active_mask()]+=2
  torch.testing.assert_close(p.evaluate(*x,z)['logp'],p.evaluate(*x,a['latent'])['logp'])
  (-p.evaluate(*x,a['latent'].detach())['logp']*torch.tensor([1.,-1.])).sum().backward()
  for f in ('index','middle'):self.assertGreater(float(p.core.finger_heads[f][-1].bias.grad.abs().sum()),0)
 def test_phase_selector_and_independent_future_slots(self):
  e,v=self.make()
  for t,want in ((0.,0),(.5,0),(1.1,0),(3.5,0),(4.6,1),(5.6,1)):
   e.clock[:]=round(t*240);self.assertEqual(e.selected_target()[0].tolist(),[want,want])
  e.clock[:]=round(3.5*240);sel=e._finger_targets(e._score_time());self.assertEqual(sel['indices'][:,0,0].tolist(),[0,0]);self.assertEqual(sel['indices'][:,1,0].tolist(),[1,1])
  e.note['contact_streak'][1]=.123;e.reset([0],fixture(2)[1]);torch.testing.assert_close(e.note['contact_streak'][1],torch.full((2,),.123,dtype=e.note['contact_streak'].dtype))
 def test_optional_noise_changes_only_active_pair_distribution(self):
  e,v=self.make();x=e.observation();inputs=[x[k] for k in ('state','events','mask','priority_events','priority_mask')]
  base=rt.TransitionPolicy(x['state'].shape[-1],size='small',contract=e.contract,natural_press=v['natural_press'],transition=v['transition'])
  import copy
  for name,std,floor in (('narrow',.105,.07),('broad',.20,.13)):
   cfg=copy.deepcopy(v['transition']);cfg['noise_profile']=name;bias=copy.deepcopy(v['natural_press']);bias.update(finger_initial_std=std,finger_std_floor=floor);contract=copy.deepcopy(e.contract);contract['transition']=cfg;contract['natural_press']=bias
   m=rt.TransitionPolicy(x['state'].shape[-1],size='small',contract=contract,natural_press=bias,transition=cfg);m.load_state_dict(base.state_dict())
   with torch.no_grad():m.core.finger_log_std[:8].fill_(torch.log(torch.tensor(std)))
   a,b=base(*inputs),m(*inputs);torch.testing.assert_close(a['mean'],b['mean']);torch.testing.assert_close(a['reward_value'],b['reward_value']);torch.testing.assert_close(a['log_std'][:,:17],b['log_std'][:,:17]);torch.testing.assert_close(b['log_std'][:,17:25].exp(),torch.full((2,8),std))
   with torch.no_grad():m.core.finger_log_std[:8].fill_(-5)
   torch.testing.assert_close(m(*inputs)['log_std'][:,17:25].exp(),torch.full((2,8),floor))
 def test_pair_diagnostics_reset_and_no_reward_mutation(self):
  import copy
  e,v=self.make();e.begin_control(torch.zeros(2,39))
  for i in range(4):
   snap=copy.deepcopy(fixture(2)[1]);snap['physics_step']=i+1;e.substep(snap)
  self.assertTrue(torch.isfinite(e.pair_pad_min).all());self.assertTrue((e.pair_pad_min>=0).all());old=e.pair_pad_min[1].clone();e.end_control();e.reset([0],fixture(2)[1]);self.assertTrue(torch.isinf(e.pair_pad_min[0]));torch.testing.assert_close(e.pair_pad_min[1],old)
if __name__=='__main__':unittest.main(verbosity=2)
