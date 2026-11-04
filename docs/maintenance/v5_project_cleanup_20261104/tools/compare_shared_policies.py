import sys,torch
from guitar_learning.training.compact_strike import CompactStrikePolicy
from guitar_learning.training.whole_body import WholeBodyPolicy
from guitar_learning.tests.test_compact_strike_policy import contract as sc,inputs as si
from guitar_learning.tests.test_whole_body_policy import contract as wc,inputs as wi
from guitar_learning.gpu.compact_strike import STATE_DIM as SD
from guitar_learning.gpu.whole_body import STATE_DIM as WD
torch.set_num_threads(1)
results={}
for name,cls,dim,contract,inputs in [('strike',CompactStrikePolicy,SD,sc,si),('whole',WholeBodyPolicy,WD,wc,wi)]:
 torch.manual_seed(297)
 model=cls(dim,contract=contract());data=inputs()
 results[name]=dict(architecture=model.architecture,state_dict={k:v.clone() for k,v in model.state_dict().items()},output=model.act(*data))
if sys.argv[1]=='save':torch.save(results,sys.argv[2]);print('saved',list(results))
else:
 old=torch.load(sys.argv[2],weights_only=False)
 def compare(a,b):
  if isinstance(a,torch.Tensor):torch.testing.assert_close(a,b,rtol=0,atol=0)
  elif isinstance(a,dict):
   assert a.keys()==b.keys()
   for k in a:compare(a[k],b[k])
  elif isinstance(a,(tuple,list)):
   assert len(a)==len(b)
   for x,y in zip(a,b):compare(x,y)
  else:assert a==b,(a,b)
 compare(old,results);print('EXACT SHARED ORACLE MATCH strike + whole_body')
