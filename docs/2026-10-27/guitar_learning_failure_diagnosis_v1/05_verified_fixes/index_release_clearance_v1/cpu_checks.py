"""Small original-geometry/pose and actual callback boundary CPU checks."""
import ast
from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
    from guitar_learning.gpu.geometry import apply,conjugate
    torch.set_num_threads(1);assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    source=probe.support();pad=load_fingertip_pad();valid=torch.from_numpy(pad['valid']);assert valid.shape==(4,128) and bool(valid.all())
    points=torch.zeros(2,4,128,3);points[...,0]=.02;points[...,1]=.035
    points[:,0,0,0]=0;points[:,0,1,0]=.001
    normals=torch.zeros_like(points);normals[...,2]=-1;normals[:,0,0,2]=1
    starts=torch.zeros(2,6,3);ends=starts.clone();ends[:,:,1]=1
    frets=torch.zeros(2,23,3);frets[:,:,1]=torch.arange(23)*.01
    plane=torch.tensor([0.,0.,1.,0.]);loaded=torch.ones(2,4,dtype=torch.bool)
    frozen=[x.clone() for x in (points,normals,valid,starts,ends,frets,loaded,plane)];rng=torch.get_rng_state().clone()
    per,agg,residual=source.geometry(points,normals,valid,starts,ends,frets,loaded,plane,2,4)
    assert agg['sample_index'].tolist()==[0,0] and not per['facing_geometry'][:,0].any() and bool(per['facing_geometry'][:,1].all()) and bool(agg['positive'].all())
    for x,before in zip((points,normals,valid,starts,ends,frets,loaded,plane),frozen):assert torch.equal(x,before)
    assert torch.equal(torch.get_rng_state(),rng)
    # Original rotation/plane/inset/same-sample/immutability regression module.
    from guitar_learning.tests import test_gpu_fingertip_pad
    suite=unittest.defaultTestLoader.loadTestsFromModule(test_gpu_fingertip_pad);stream=io.StringIO();result=unittest.TextTestRunner(stream=stream).run(suite);assert result.wasSuccessful(),stream.getvalue()
    body=torch.zeros(128,4,13);body[:,:,3:7]=torch.tensor([.1,.2,.3,.9])/torch.tensor([.1,.2,.3,.9]).norm();body[:,:,:3]=torch.tensor([.2,-.1,.4])
    guitar=torch.zeros(128,13);guitar[:,3:7]=torch.tensor([-.2,.1,.05,.95])/torch.tensor([-.2,.1,.05,.95]).norm();guitar[:,:3]=torch.tensor([.1,.1,.2])
    env=SimpleNamespace(device=torch.device('cpu'),clock=torch.full((128,),692,dtype=torch.long),pad_local=torch.from_numpy(pad['points_local']).float(),pad_normals=torch.from_numpy(pad['normals_local']).float(),pad_valid=valid,
        pad_indices=torch.arange(4),body_names=['human/LH:'+x+'3' for x in ('index','middle','ring','pinky')],body=body,guitar_body=guitar,
        starts=starts[:1].expand(128,6,3).clone(),ends=ends[:1].expand(128,6,3).clone(),frets=frets[:1].expand(128,23,3).clone(),press_plane=plane,
        loaded=torch.ones(128,4,dtype=torch.bool),snapshot=dict(reset_body_snapshot=torch.zeros(128,dtype=torch.bool),contact_force=torch.ones(128,4,3)),
        failure=torch.zeros(128,1,dtype=torch.bool),wrist_failure=torch.zeros(128,dtype=torch.bool),wrist_severe_failure=torch.zeros(128,dtype=torch.bool),
        candidate=torch.zeros(128,9,dtype=torch.bool),wrong=torch.zeros(128,9,dtype=torch.bool),note=dict(released=torch.zeros(128,9,dtype=torch.bool),release_s=torch.zeros(128,9)),
        contact_geometry=torch.zeros(128,9,dtype=torch.bool),contact_facing=torch.zeros(128,9,dtype=torch.bool),contact_loaded_target=torch.zeros(128,9,dtype=torch.bool),surface_distance=torch.zeros(128,9),surface_sample=torch.zeros(128,9,dtype=torch.long),surface_height=torch.zeros(128,9),surface_alignment=torch.zeros(128,9),
        string=torch.tensor([0,0,0,0,2,0,0,1,1]),fret=torch.tensor([1,1,1,1,4,1,1,5,5]),finger=torch.ones(9,dtype=torch.long),
        contract=dict(observation=dict(surface_geometry=dict(pad=pad['contract']))))
    env._local_time=lambda:env.clock.double()/240;env._score_time=lambda:env._local_time()+2.4497
    env.failure[0]=True;env.snapshot['reset_body_snapshot'][1]=True
    pool=SimpleNamespace(num_envs=128,spec=dict(view=dict(source_indices=[4,7,8])),environment=env,first=torch.zeros(128,dtype=torch.bool))
    record=dict(first_attempt=np.array([True,True,False,True]),start_clock=np.full(4,688),prior_failure=np.zeros(4,dtype=bool))
    audit=dict(rows=[],after_calls=0);source.capture(probe,pool,record,audit)
    assert [r['env_id'] for r in audit['rows']]==[0,1,3] and audit['rows'][0]['post_failure'] and not audit['rows'][1]['valid_snapshot'] and np.isnan(audit['rows'][1]['point_distance']).all()
    def matrix(q):
        x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    row=audit['rows'][0];expected=((audit['static']['local_points'].astype(np.float64)@matrix(row['distal_pose'][3:].astype(np.float64)).T+row['distal_pose'][:3]-row['guitar_pose'][:3])@matrix(row['guitar_pose'][3:].astype(np.float64)))
    transform_residual=float(np.max(np.abs(expected-row['points_G'])));assert transform_residual<2e-7
    assert source.selected_rows(record,np.array([688,692,920,924])).tolist()==[1]
    for clock in (688,924):
        env.clock.fill_(clock);before=len(audit['rows']);source.capture(probe,pool,record,audit);assert len(audit['rows'])==before
    env.clock.fill_(692);collector=probe.goal.source.source.support();old_after=collector.after;seen=[]
    def original(*args):seen.append(args);return ['original']
    with patch.object(collector,'after',original),patch.object(torch.nn.Module,'__init__',side_effect=AssertionError('NN forbidden')),patch.object(torch,'load',side_effect=AssertionError('load forbidden')):
        with source.observer(probe,audit):assert collector.after(probe.goal,pool,record)==['original']
        assert collector.after is original and audit['after_calls']==1
        with patch.object(source,'capture',side_effect=ValueError('observer first')):
            with source.observer(probe,audit):
                try:collector.after(probe.goal,pool,record)
                except ValueError as e:assert str(e)=='observer first'
                else:raise AssertionError('Observer error lost')
        assert len(seen)==2 and collector.after is original
    assert collector.after is old_after and torch.equal(torch.get_rng_state(),rng)
    # Real scope restores aliases in both modes without invoking numerical/native pool creation.
    aliases=(probe.goal.output,probe.goal.gate,probe.noise.output,probe.noise.gate)
    for mode in probe.MODES:
        state=dict(rows=[],after_calls=0)
        try:
            with probe.execution_scope(mode,({},set()),state):raise ValueError('native primary')
        except ValueError as e:assert str(e)=='native primary'
        assert (probe.goal.output,probe.goal.gate,probe.noise.output,probe.noise.gate)==aliases and state['producer_aliases_restored'] and state['observer_alias_restored']
    with tempfile.TemporaryDirectory() as temp:
        folder=Path(temp);(folder/'goal_codec_report.json').write_text('{}')
        with patch.object(probe,'output',return_value=folder),patch.object(np,'savez_compressed',side_effect=ValueError('raw first')),patch.object(probe.grid,'read',side_effect=OSError('report read second')),redirect_stderr(io.StringIO()) as stderr:
            try:probe.finish('reference',audit,True,None)
            except ValueError as e:assert str(e)=='raw first'
            else:raise AssertionError('First failure lost')
            assert 'report read second' in stderr.getvalue()
        for mode in probe.MODES:
            with patch.object(probe,'output',return_value=folder),patch.object(probe,'gate',side_effect=AssertionError('late gate')) as gate:
                try:probe.launch(mode)
                except FileExistsError:pass
                else:raise AssertionError('Existing output admitted')
                gate.assert_not_called()
    for name in ('probe.py','surface.py','cpu_checks.py'):ast.parse((probe.HERE/name).read_text(),feature_version=8)
    return dict(CPU_only=True,GPU_executed=False,models_created=0,models_loaded=0,original_geometry_tests=result.testsRun,source_valid_all4x128=True,
        P1_P128_distance_max_abs_m=float(residual.max()),nearest_not_witness=True,independent_pose_transform_max_abs_m=transform_residual,
        source_and_rng_unchanged=True,first_failure_endpoint_retained=True,reset_snapshot_invalid_not_native=True,clock_window=[692,920],max_rows=232,
        actual_after_delegate_and_restore=True,both_mode_aliases_restored=True,typed_raw_report_read_first_error_preserved=True,output_rejected_before_gate=True)
