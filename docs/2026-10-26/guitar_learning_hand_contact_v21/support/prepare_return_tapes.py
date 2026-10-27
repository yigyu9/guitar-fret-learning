"""New command tapes for a measured B return budget; never load physical state."""
from pathlib import Path
import json,hashlib
import numpy as np
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.core.control import ACTIVE_NAMES,LEFT_HAND_NAMES
from guitar_learning.gpu.finger_reward import B_PREPARATION_INPUT_DEGREES,B_PREPARATION_SPREAD_DEGREES
ROOT=Path('/home/ajou/yigyu/3');PHASE=ROOT/'docs/2026-10-26/guitar_learning_hand_contact_v21'
source=ROOT/'docs/2026-10-25/guitar_learning_v20_A500/evaluation_repeat1/poses_env0000.npz'
old=np.load(source);contract=load_prepared_reset_contract();names=contract['initial']['joint_names']
joints=[names.index(n) for n in LEFT_HAND_NAMES];actions=[ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES]
goal=np.array(contract['target105'],dtype=np.float32)[joints].copy()
goal[5:]=np.deg2rad(np.array([[x,z,p,d] for (x,p,d),z in zip(B_PREPARATION_INPUT_DEGREES,B_PREPARATION_SPREAD_DEGREES)],dtype=np.float32)).flatten()
prefix=720;append=180
for thumb in ('held','return_initial'):
 a=old['action'][:prefix+1].copy();targets=old['target'][:prefix+1].copy();target=targets[-1].copy();g=goal.copy()
 if thumb=='held':g[:5]=target[joints[:5]]
 aa=[];tt=[]
 for _ in range(append):
  action=a[-1].copy();action[actions]=np.clip((g-target[joints])*(60./4.),-1,1)
  target[joints]+=action[actions]*(4./60.)
  aa.append(action);tt.append(target.copy())
 action=np.concatenate((a,np.stack(aa)));target=np.concatenate((targets,np.stack(tt)))
 path=PHASE/'support'/('B_return_thumb_'+thumb+'.npz')
 np.savez_compressed(path,action=action,target=target,clock=np.arange(len(action))*4)
 (path.with_suffix('.json')).write_text(json.dumps(dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
   prefix_controls=prefix,return_controls=append,return_start_s=12.,thumb=thumb,
   scope='Actions only: original first12s then nonthumb direct B target at unchanged4rad/s; other39 action channels held at preceding action; thumb either keeps previous target or returns to prepared target. No q/body injection.'),indent=2))
 print(path)
