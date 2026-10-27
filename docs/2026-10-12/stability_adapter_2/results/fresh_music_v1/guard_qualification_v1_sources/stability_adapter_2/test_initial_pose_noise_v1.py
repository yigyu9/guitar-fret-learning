import json
from pathlib import Path
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from stability_adapter_2.initial_pose_noise_v1 import PoseBank,fit_hands,sha

def fixture_fk():
    names=[s+'_'+part+'_'+axis for s in ('L','R') for part in ('Thorax','Shoulder','Elbow','Wrist') for axis in 'xyz']+['Torso_x','LH:index1']
    q=np.zeros(len(names));q[-2:]=[.2,.3]
    def fk(values):
        return {s+'H:palm':(np.array([.1 if s=='L' else -.1,0.,.8])+values[i:i+3],Rotation.from_rotvec(values[i+3:i+6])) for s,i in [('L',0),('R',12)]}
    return names,q,fk

def test_rigid_hand_goals_and_fixed_channels():
    names,q,fk=fixture_fk();dp=np.array([.003,-.002,.004]);rv=np.array([.5,-.5,.2])
    out,p,r,goals,metrics=fit_hands(fk,q,names,np.full(q.size,-1),np.full(q.size,1),np.array([0.,0.,.8]),Rotation.identity(),dp,rv)
    assert np.array_equal(out[-2:],q[-2:])
    assert np.max(abs(out-q))<=.15
    assert all(v['position_error_m']<1e-5 and v['orientation_error_deg']<1e-3 for v in metrics.values())
    for n,(tp,tr) in goals.items():assert np.allclose(tp,p+r.apply(fk(q)[n][0]-[0,0,.8]))

def test_zero_and_invalid_noise():
    names,q,fk=fixture_fk();args=(fk,q,names,np.full(q.size,-1),np.full(q.size,1),np.zeros(3),Rotation.identity())
    out,*_=fit_hands(*args,np.zeros(3),np.zeros(3));assert np.allclose(out,q)
    with pytest.raises(ValueError):fit_hands(*args,[0,0,-.001],[0,0,0])
    with pytest.raises(ValueError):fit_hands(*args,[0,0,0],[0,2,0])

def bank_file(tmp_path):
    source=tmp_path/'input.json';source.write_text('{}');path=tmp_path/'bank.json'
    path.write_text(json.dumps({'schema':'sa2_coupled_initial_pose_bank_v1','entries':[{'validated_native':True,'source_clear':True,'config_path':str(source)} for _ in range(4)],'input_sha256':{str(source):sha(source)}}));return path,source

def test_seeded_independent_sampling_and_immutability(tmp_path):
    path,_=bank_file(tmp_path);a=PoseBank(path,10);b=PoseBank(path,10);c=PoseBank(path,11)
    seq=lambda bank:[bank.sample()[1]['index'] for _ in range(16)]
    sa,sb,sc=seq(a),seq(b),seq(c);assert sa==sb and sa!=sc and len(set(sa))>1
    entry,_=a.sample(0);entry['source_clear']=False;assert a.sample(0)[0]['source_clear']
    with pytest.raises(ValueError):a.sample(-1)

def test_bank_source_mutation_rejected(tmp_path):
    path,source=bank_file(tmp_path);source.write_text('{"changed":true}')
    with pytest.raises(ValueError):PoseBank(path,1)
