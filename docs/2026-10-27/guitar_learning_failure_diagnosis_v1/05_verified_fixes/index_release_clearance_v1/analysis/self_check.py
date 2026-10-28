"""Small CPU geometry fixture; no runtime files, native scene or model reads."""
from pathlib import Path
import sys


def check():
    sys.path.insert(0,str(Path(__file__).resolve().parents[6]))
    import torch
    import unittest
    from guitar_learning.gpu.fingertip_pad import pad_target_geometry
    from guitar_learning.tests.test_gpu_fingertip_pad import PadGeometryTests
    torch.set_num_threads(1)
    n,p=3,128
    points=torch.zeros(n,4,p,3,dtype=torch.float64);points[...,0]=.006;points[...,1]=.5;points[...,2]=.001
    normals=torch.zeros_like(points);normals[...,2]=1
    points[:,0,0]=torch.tensor([0.,.5,.0001]);points[:,0,1]=torch.tensor([0.,.5,.002]);normals[:,0,1,2]=-1
    points[2,0,0,1]=.401;points[2,0,1,1]=.599
    speeds=torch.zeros_like(points);speeds[...,0]=torch.arange(p)*.0001
    valid=torch.ones(4,p,dtype=torch.bool);loaded=torch.ones(n,4,dtype=torch.bool);loaded[1,0]=False
    starts=torch.zeros(n,6,3,dtype=torch.float64);ends=starts.clone();ends[...,1]=1
    x=dict(points=points,normals=normals,velocities=speeds,valid=valid,starts=starts,ends=ends,
        low=torch.full((n,1),.4,dtype=torch.float64),high=torch.full((n,1),.6,dtype=torch.float64),
        strings=torch.tensor([2]),fingers=torch.tensor([1]),loaded=loaded,plane=torch.tensor([0.,0.,1.,0.],dtype=torch.float64))
    before={k:v.clone() for k,v in x.items()};aggregate=pad_target_geometry(**x)
    flat=dict(x)
    for k in ('points','normals','velocities'):flat[k]=x[k].permute(0,2,1,3).reshape(n*p,4,1,3)
    flat['valid']=torch.ones(4,1,dtype=torch.bool)
    for k in ('starts','ends','low','high','loaded'):flat[k]=x[k].repeat_interleave(p,0)
    each=pad_target_geometry(**flat);distance=each['distance'].reshape(n,p);nearest=distance.argmin(1)
    assert torch.equal(aggregate['sample_index'][:,0],nearest)
    for k in ('position_geometry','facing_geometry','positive'):
        assert torch.equal(aggregate[k][:,0],each[k].reshape(n,p).any(1)),k
    for k in ('distance','normal_cos','signed_height','delta','velocity'):
        shape=(n,p)+tuple(each[k].shape[2:]);values=each[k].reshape(shape)
        torch.testing.assert_close(aggregate[k][:,0],values[torch.arange(n),nearest],rtol=0,atol=0)
    assert nearest[0]==0 and not each['facing_geometry'].reshape(n,p)[0,0] and aggregate['positive'][0,0]
    assert aggregate['facing_geometry'][1,0] and not aggregate['positive'][1,0]
    assert not aggregate['position_geometry'][2,0]
    assert all(torch.equal(x[k],v) for k,v in before.items())
    names=('test_real_cell_is_inset_not_expanded_and_nearest_is_clamped','test_plane_normalization_and_oblique_plane_geometry',
        'test_position_and_facing_must_hold_for_same_sample','test_eligible_facing_sample_need_not_be_nearest_sample')
    result=unittest.TestResult();unittest.TestSuite(PadGeometryTests(name) for name in names).run(result)
    assert result.wasSuccessful(),(result.errors,result.failures)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    print('CPU PASS: P128/P1 aggregate·nearest≠witness·load/sourcevalid/입력불변, 원geometry4검사; actual자료/GPU/model0')


if __name__=='__main__':check()
