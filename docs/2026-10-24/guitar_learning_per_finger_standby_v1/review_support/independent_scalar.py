"""Independent CPU scalar reference for v17 per-finger B gating; no simulator."""
from pathlib import Path
import sys, math, json
import numpy as np
import torch
from scipy.spatial.transform import Rotation
sys.path.insert(0,str(Path(__file__).resolve().parents[4]))
from guitar_learning.gpu.finger_reward import finger_preparation_reward

torch.set_num_threads(1)
rng=np.random.RandomState(217)
N,M=128,13
assigned=np.array([1,2,4,1,4,2,1,2,4,1,4,1,2])
onset=rng.uniform(3.,15.,M);end=onset+rng.uniform(.1,1.,M);press=onset-.3
now=rng.uniform(-1.,18.,N)
reference=np.array([[25.,35.,12.],[28.,38.,14.],[31.,41.,16.],[34.,44.,18.]])
for f,z in enumerate([-14.,-3.,3.,10.]):
 x=reference[f,0];a=math.radians(math.hypot(x,z));reference[f,0]=math.degrees(math.atan2(x/math.hypot(x,z)*math.sin(a),math.cos(a)))
angles=np.deg2rad(reference)[None]+rng.uniform(-.9,.9,(N,4,3))
palm=Rotation.random(N,random_state=rng);segments=np.zeros((N,4,3,4))
for f in range(4):
 current=palm
 for j in range(3):
  current=current*Rotation.from_rotvec(np.column_stack([angles[:,f,j],np.zeros((N,2))]))
  segments[:,f,j]=current.as_quat()
contact=rng.rand(N,4)<.13;distance=rng.uniform(.045,.2,(N,M))
for row in range(N):distance[row,row%M]=[.04,np.nan,np.inf,.040001][row%4]
data=dict(now=torch.tensor(now),onset=torch.tensor(onset),end=torch.tensor(end),press=torch.tensor(press),finger=torch.tensor(assigned),palm_quaternion=torch.tensor(palm.as_quat()),segment_quaternion=torch.tensor(segments),contact=torch.tensor(contact),distance=torch.tensor(distance))
result=finger_preparation_reward(**data)
gate=np.ones((N,4));quality=np.zeros((N,4));rate=np.zeros(N)
for row in range(N):
 for f in range(4):
  own=np.where(assigned==f+1)[0]
  busy=max([min(max(0.,min(1.,(now[row]-(press[k]-2.25))/.25)),max(0.,min(1.,(end[k]+.25-now[row])/.25))) for k in own] or [0.])
  near=any(not math.isfinite(distance[row,k]) or distance[row,k]<=.04 for k in own)
  gate[row,f]=(1-busy)*(not(contact[row,f] or near))
  excess=[max(abs(math.degrees(angles[row,f,j])-reference[f,j])-15.,0.) for j in range(3)]
  quality[row,f]=math.exp(-sum(x*x for x in excess)/30.**2)
 rate[row]=.01*sum(gate[row,f]*quality[row,f] for f in range(4))/4.
errors={key:float(np.max(abs(actual.detach().numpy()-expected))) for key,actual,expected in [('gate',result['gate'],gate),('quality',result['quality'],quality),('rate',result['rate'],rate)]}
assert errors['gate']<1e-13 and errors['quality']<1e-13 and errors['rate']<1e-14,errors
assert ((rate>=0)&(rate<=.01)).all()
for f in range(4):
 changed=dict(data);mask=data['contact'].clone();mask[:,f]=~mask[:,f];changed['contact']=mask;again=finger_preparation_reward(**changed)
 keep=[j for j in range(4) if j!=f];assert torch.equal(again['gate'][:,keep],result['gate'][:,keep]);assert torch.equal(again['quality'],result['quality'])
# Independent scalar check of environment's own-segment and assigned-event boolean routing.
loads=rng.rand(N,4,3)<.07;events=[rng.rand(N,M)<.06 for _ in range(4)]
vector=torch.tensor(loads).any(-1)|((torch.tensor(events[0]|events[1]|events[2]|events[3])[:,None])&(torch.tensor(assigned)[None]==torch.arange(1,5)[:,None])[None]).any(-1)
expected=np.array([[any(loads[row,f]) or any(any(e[row,k] for e in events) for k in range(M) if assigned[k]==f+1) for f in range(4)] for row in range(N)])
assert np.array_equal(vector.numpy(),expected)
print(json.dumps(dict(passed=True,scalar_gate_quality_cells=N*4,scalar_rate_rows=N,cross_finger_contact_isolation_cells=N*4,environment_contact_routing_cells=N*4,maximum_absolute_errors=errors)))
