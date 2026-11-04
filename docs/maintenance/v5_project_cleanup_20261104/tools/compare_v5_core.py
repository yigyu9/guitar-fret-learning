import sys, copy, torch
from unittest.mock import patch
from guitar_learning.gpu.compact_press_v5 import CompactPressV5Environment
from guitar_learning.training.compact_press_v5 import CompactPressV5Policy
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.song.task import ScoreTask, ScoreTarget

torch.set_num_threads(1)
SKILL=dict(schema='guitar_learning.finger_skill.v3', phase='J',scope='scheduled',hold_ticks=1,exploration='independent',planned_transitions=400,full_song_after=100)
notes=ScoreTask(tuple(ScoreTarget(str(i), str(i), 2-i, 6+i, i+1, 1, .02+i*.01, .07+i*.02, .01+i*.01, .02+i*.01,.07+i*.02) for i in range(2)))
def clone(value):
    if isinstance(value,torch.Tensor):return value.detach().clone()
    if isinstance(value,dict):return {k:clone(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return type(value)(clone(v) for v in value)
    return copy.deepcopy(value)
all_results={}
for profile in ('corrected','preparation','full_hold','combined'):
 for pelvis in (False,True):
  class Environment(CompactPressV5Environment):
   include_pelvis=pelvis
   improvement_profile=profile
  metadata,snapshot=fixture(2)
  with patch('guitar_learning.gpu.environment.make_task',return_value=notes):
   env=Environment(metadata,bundle=BUNDLE,song=dict(SONG,left_fraction=1. if profile in ('full_hold','combined') else .4),skill=SKILL,device='cpu')
  env.set_evaluation(True,full_song=True)
  observation=env.reset(range(2),snapshot)
  torch.manual_seed(97)
  model=CompactPressV5Policy(473 if pelvis else 464,contract=env.contract)
  result=dict(contract=clone(env.contract),architecture=clone(model.architecture),weights=clone(model.state_dict()),initial=clone(observation),policy=clone(model.act(**observation)))
  ticks=[]
  for number in range(8):
   env.begin_control(torch.zeros(2,39))
   for substep in range(4):
    # 실제 패드 후보, 오압현, 하중 소실을 별도로 교차시킨다.
    loaded=torch.tensor([[number<5,number%2==0],[number<4,number%3==0]])
    wrong=torch.tensor([[number==2,False],[False,number==3]])
    def contacts(loaded=loaded,wrong=wrong):
     env.contact_loaded_target[:]=loaded
     return loaded & ~wrong,wrong
    env._contacts=contacts
    env.substep(dict(snapshot,physics_step=env.clock+1))
   ticks.append(clone(env.end_control()))
  result['ticks']=ticks
  result['episodes']=[clone(env._episode(0,False)),clone(env._episode(1,True))]
  before=clone(env.observation())
  env.reset_reward_window(); env.reset([0],snapshot)
  result['partial_reset']=clone(env.observation())
  all_results[profile,str(pelvis)]=result
if sys.argv[1]=='save':torch.save(all_results,sys.argv[2]);print('saved',len(all_results))
else:
 old=torch.load(sys.argv[2],map_location='cpu',weights_only=False)
 count=[0]
 def compare(a,b,path=''):
  count[0]+=1
  if isinstance(a,torch.Tensor):torch.testing.assert_close(a,b,rtol=0,atol=0,equal_nan=True,msg=path)
  elif isinstance(a,dict):
   assert a.keys()==b.keys(),path
   for k in a:compare(a[k],b[k],path+'/'+str(k))
  elif isinstance(a,(list,tuple)):
   assert len(a)==len(b),path
   for i,(x,y) in enumerate(zip(a,b)):compare(x,y,path+'/'+str(i))
  else:assert a==b,(path,a,b)
 compare(old,all_results)
 print('EXACT CPU ORACLE MATCH',len(all_results),'cases',count[0],'comparisons')
