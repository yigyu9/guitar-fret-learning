import ast,io,importlib.util,pathlib,copy,unittest,torch
from unittest.mock import patch
D=pathlib.Path(__file__).resolve().parents[2];L=D/'로그분석'
spec=importlib.util.spec_from_file_location('pair_tests',D/'tests/test_pair_runtime.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
from guitar_learning.gpu.environment import TensorSongEnvironment
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.tests.test_gpu_environment import fixture
from guitar_learning.training.training_log_io import dumps
class ObserverParity(unittest.TestCase):
 def test_same_outputs_states_rng(self):
  torch.set_num_threads(1);a,_=p.PairTests().make();b,_=p.PairTests().make()
  for e in (a,b):
   e.begin_control(torch.zeros(2,39))
   for i in range(4):s=copy.deepcopy(fixture(2)[1]);s['physics_step']=i+1;e.substep(s)
  tree=ast.parse((L/'tools/observe_evaluate.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('observed','observed_components')];ns={'original':TensorSongEnvironment.end_control,'original_components':FingerSkillEnvironment._reward_components,'torch':torch,'stream':io.StringIO(),'dumps':dumps};exec(compile(ast.Module(body=nodes,type_ignores=[]),'observer','exec'),ns)
  before=torch.get_rng_state();aa=a.end_control();mid=torch.get_rng_state()
  with patch.object(TensorSongEnvironment,'end_control',ns['observed']),patch.object(FingerSkillEnvironment,'_reward_components',ns['observed_components']):bb=b.end_control()
  self.assertTrue(torch.equal(before,mid));self.assertTrue(torch.equal(mid,torch.get_rng_state()))
  for i in (1,2,3,4):torch.testing.assert_close(aa[i],bb[i],rtol=0,atol=0)
  for k in aa[0]:torch.testing.assert_close(aa[0][k],bb[0][k],rtol=0,atol=0)
  for k in a.episode_reward_terms:torch.testing.assert_close(a.episode_reward_terms[k],b.episode_reward_terms[k],rtol=0,atol=0)
  self.assertTrue(ns['stream'].getvalue())
if __name__=='__main__':unittest.main(verbosity=2)
