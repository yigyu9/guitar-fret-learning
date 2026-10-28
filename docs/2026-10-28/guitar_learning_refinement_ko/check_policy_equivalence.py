import copy,importlib.util,json
from pathlib import Path
import torch
from guitar_learning.training import policy as new
from guitar_learning.core.control import ACTIVE_NAMES
root=Path('/home/ajou/yigyu/3/guitar_learning'); old=root/'archive/20261028_before_refinement_ko/guitar_learning'
torch.set_num_threads(1)
def load(path,name):
 spec=importlib.util.spec_from_file_location(name,str(path));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
modules={k:load(old/(path+'.py'),'old_'+k) for k,path in [('policy','training/policy'),('specialist','training/policy'),('finger','training/policy')]}
base={'schema':'guitar_learning.training.v1','observation':{'dimension':5},'action':{'dimension':39},'task':{'source':'synthetic_cpu_test'},'reward':{},'termination':{}}
def finger_contract(phase,exploration,simplified=False):
 fields=[]
 for finger in new.FINGERS:
  joints=['LH:'+finger+s for s in ('1_x','1_z','2','3')]
  fields.extend(b+'.'+j for b in ('q_offset','q_velocity','target_error') for j in joints)
  fields.extend('finger_posture.'+finger+'.'+j+'.'+t for j in ('MCP','PIP','DIP') for t in ('sin','cos'))
  fields.extend('finger_posture.'+finger+'.'+n for n in ('valid','standby_gate'))
 fields.extend(b+'.'+j for b in ('q_offset','q_velocity','target_error','previous_action') for j in ACTIVE_NAMES[:17])
 tail=new.PHASE_FIELDS+(new.WRIST_TERMINATION_FIELDS if simplified else ())
 dim=561 if simplified else 557
 fields.extend('synthetic_'+str(i) for i in range(dim-len(fields)-len(tail)))
 fields.extend(tail)
 c=copy.deepcopy(base);c['observation'].update(fields=fields,dimension=dim,priority_slots=8,finger_targets={'schema':'guitar_learning.left_finger_targets.v1','slots':[f+'_'+k for f in new.FINGERS for k in ('tracking','next')]});c['action']['names']=list(ACTIVE_NAMES);c['native_backend']={'pipeline':'gpu'};c['task']['finger_skill']={'schema':'guitar_learning.finger_skill.v2' if simplified else 'guitar_learning.finger_skill.v1','phase':phase,'exploration':exploration};return c
cases=[('Policy',modules['policy'].Policy,new.Policy,dict(state_dim=5,size='small',contract=base)),('SpecialistPolicy',modules['specialist'].SpecialistPolicy,new.SpecialistPolicy,dict(state_dim=5,size='small',contract=base,role='joint'))]
for phase in ('R','F','J'):
 for exploration in ('independent','correlated'):
  cases.append(('FingerSkillPolicy_'+phase+'_'+exploration,modules['finger'].FingerSkillPolicy,new.FingerSkillPolicy,dict(state_dim=557,size='small',contract=finger_contract(phase,exploration),phase=phase,exploration=exploration)))
cases.append(('FingerSkillPolicy_J_v2',modules['finger'].FingerSkillPolicy,new.FingerSkillPolicy,dict(state_dim=561,size='small',contract=finger_contract('J','independent',True),phase='J',exploration='independent')))
result=[]
for name,old_type,new_type,kw in cases:
 torch.manual_seed(142);a=old_type(**kw);rng_a=torch.get_rng_state();torch.manual_seed(142);b=new_type(**kw);rng_b=torch.get_rng_state()
 assert a.architecture==b.architecture,name
 assert torch.equal(rng_a,rng_b),name
 sa,sb=a.state_dict(),b.state_dict(); assert list(sa)==list(sb),name
 assert all(torch.equal(sa[k],sb[k]) for k in sa),name
 priority=8 if name.startswith('FingerSkillPolicy') else 2
 data=(torch.randn(2,kw['state_dim']),torch.randn(2,3,24),torch.ones(2,3,dtype=torch.bool),torch.randn(2,priority,24),torch.ones(2,priority,dtype=torch.bool))
 torch.manual_seed(617);oa=a.act(*data);torch.manual_seed(617);ob=b.act(*data)
 assert oa.keys()==ob.keys(),name
 assert all(torch.equal(oa[k],ob[k]) for k in oa),name
 assert [next(k for k,v in a.named_parameters() if v is x) for x in a.value_parameters()]==[next(k for k,v in b.named_parameters() if v is x) for x in b.value_parameters()],name
 result.append(dict(case=name,exact_value_parameter_order=True,exact_architecture=True,exact_parameter_keys_and_values=True,exact_rng=True,exact_actions_values_probabilities=True))
 print(name,'PASS')
Path('/tmp/guitar_refinement_ko_20261028/policy_equivalence.json').write_text(json.dumps(result,indent=2))
