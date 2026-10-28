"""Read-only index3 source128 finite-cell samples, at original60Hz endpoints."""
from contextlib import contextmanager
import sys
import numpy as np
import torch
from guitar_learning.gpu.geometry import apply,conjugate
from guitar_learning.gpu.fingertip_pad import pad_target_geometry
from guitar_learning.gpu.press_surface import project_press_strings

START_CLOCK,END_CLOCK=692,920


def geometry(points,normals,valid,starts,ends,frets,loaded,plane,string,fret):
    # Current source asset has all4*128 valid samples; no variable-mask adapter.
    assert points.shape[1:]==(4,128,3) and valid.shape==(4,128) and bool(valid.all())
    n=len(points);starts,ends=project_press_strings(starts,ends,plane)
    a,b=frets[:,fret-1,1],frets[:,fret,1];low=torch.minimum(a,b)[:,None];high=torch.maximum(a,b)[:,None]
    strings=torch.tensor([string],device=points.device);fingers=torch.ones_like(strings)
    aggregate=pad_target_geometry(points,normals,torch.zeros_like(points),valid,starts,ends,low,high,strings,fingers,loaded,plane)
    expanded=lambda x:x[:,None].expand((n,128)+x.shape[1:]).reshape((n*128,)+x.shape[1:])
    p=points.permute(0,2,1,3).reshape(n*128,4,1,3);normal=normals.permute(0,2,1,3).reshape_as(p)
    single=pad_target_geometry(p,normal,torch.zeros_like(p),valid[:,:1],expanded(starts),expanded(ends),expanded(low),expanded(high),strings,fingers,expanded(loaded),plane)
    sample={k:single[k].reshape(n,128) for k in ('distance','normal_cos','signed_height','position_geometry','facing_geometry','positive')}
    unit=plane[:3]/plane[:3].norm();start=starts[:,string];line=ends[:,string]-start;surface=points[:,0]
    projection=((surface*line[:,None]).sum(-1)-(start*line).sum(-1)[:,None])/line.square().sum(-1)[:,None]
    lateral=(surface-sample['signed_height'][...,None]*unit-start[:,None]-projection[...,None]*line[:,None]).norm(dim=-1)
    sample.update(lateral=lateral,in_cell=(surface[:,:,1]>=low+.002)&(surface[:,:,1]<=high-.002))
    nearest=aggregate['sample_index'];sample_min=sample['distance'].min(-1).values
    residual=(sample_min-aggregate['distance'][:,0]).abs()
    # Arithmetic agreement only; neither tolerance nor new fields change any predicate.
    assert bool((residual<=1e-7).all())
    for k in ('position_geometry','facing_geometry','positive'):assert torch.equal(sample[k].any(-1),aggregate[k][:,0])
    for k in ('normal_cos','signed_height'):assert torch.equal(sample[k].gather(1,nearest),aggregate[k])
    return sample,{k:v[:,0] for k,v in aggregate.items() if k not in ('delta','velocity')},residual


def selected_rows(record,clock):
    return np.flatnonzero(record['first_attempt'] & (clock>=START_CLOCK) & (clock<=END_CLOCK))


def capture(probe,pool,record,audit):
    env=pool.environment;clock=env.clock[:4].detach().cpu().numpy().copy();indices=selected_rows(record,clock)
    if not len(indices):return
    assert pool.num_envs==128 and pool.spec['view']['source_indices']==[4,7,8]
    assert bool(env.pad_valid.all()) and env.pad_valid.shape==(4,128)
    assert env.body_names[env.pad_indices[0]]=='human/LH:index3'
    if 'static' not in audit:
        audit['static']=dict(local_points=env.pad_local[0].cpu().numpy().copy(),local_normals=env.pad_normals[0].cpu().numpy().copy(),source_valid=env.pad_valid.cpu().numpy().copy(),plane=env.press_plane.cpu().numpy().copy())
        audit['pad_contract']=env.contract['observation']['surface_geometry']['pad']
    ids=torch.as_tensor(indices,device=env.device);body=env.body[ids][:,env.pad_indices];guitar=env.guitar_body[ids]
    world=body[:,:,None,:3]+apply(body[:,:,None,3:7],env.pad_local[None])
    points=apply(conjugate(guitar[:,None,None,3:7]),world-guitar[:,None,None,:3])
    normals=apply(conjugate(guitar[:,None,None,3:7]),apply(body[:,:,None,3:7],env.pad_normals[None]))
    reset=env.snapshot['reset_body_snapshot'][ids];finite=torch.isfinite(body).all((1,2))&torch.isfinite(guitar).all(1)
    valid=~reset&finite
    # Reset snapshots are prepared/stale; retain the endpoint but do not call it native geometry.
    rows=[]
    for j,i in enumerate(indices):
        row=dict(env_id=int(i),start_clock=int(record['start_clock'][i]),clock=int(clock[i]),first_attempt=bool(record['first_attempt'][i]),
            prior_failure=bool(record['prior_failure'][i]),post_failure=bool((env.failure[i].any()|env.wrist_failure[i]|env.wrist_severe_failure[i]).item()),
            reset_body_snapshot=bool(reset[j]),valid_snapshot=bool(valid[j]),time_s=float(env._local_time()[i]),source_time_s=float(env._score_time()[i]))
        assert row['clock']==row['start_clock']+4
        for name,value in dict(distal_pose=body[j,0,:7],guitar_pose=guitar[j,:7],points_G=points[j,0],normals_G=normals[j,0],
            starts_G=env.starts[i],ends_G=env.ends[i],frets_G=env.frets[i],body_loaded=env.loaded[i,env.pad_indices[0]],
            body_force_n=env.snapshot['contact_force'][i,env.pad_indices[0]],candidate=env.candidate[i,4],wrong=env.wrong[i,4],
            released=env.note['released'][i,4],release_s=env.note['release_s'][i,4],cached_distance=env.surface_distance[i,4],
            cached_sample_index=env.surface_sample[i,4],cached_signed_height=env.surface_height[i,4],cached_normal_cos=env.surface_alignment[i,4],cached_position_geometry=env.contact_geometry[i,4],cached_facing_geometry=env.contact_facing[i,4],cached_positive=env.contact_loaded_target[i,4]).items():row[name]=value.detach().cpu().numpy().copy()
        rows.append(row)
    # Original task columns remain unchanged; A is source target4, not compact column0.
    assert int(env.string[4])==2 and int(env.fret[4])==4 and int(env.finger[4])==1
    good=valid.nonzero().flatten()
    if len(good):
        sample,aggregate,residual=geometry(points[good],normals[good],env.pad_valid,env.starts[ids][good],env.ends[ids][good],env.frets[ids][good],env.loaded[ids][:,env.pad_indices][good],env.press_plane,2,4)
        for k,j in enumerate(good.tolist()):
            rows[j].update({'point_'+name:value[k].cpu().numpy().copy() for name,value in sample.items()})
            rows[j].update({'aggregate_'+name:value[k].cpu().numpy().copy() for name,value in aggregate.items()});rows[j]['aggregate_distance_residual_m']=float(residual[k])
    # All rows keep a fixed typed shape, including a possible failed/reset endpoint.
    for row in rows:
        for name in ('distance','normal_cos','signed_height','lateral'):row.setdefault('point_'+name,np.full(128,np.nan,dtype=np.float32))
        for name in ('position_geometry','facing_geometry','positive','in_cell'):row.setdefault('point_'+name,np.zeros(128,dtype=bool))
        for name in ('distance','normal_cos','signed_height'):row.setdefault('aggregate_'+name,np.float32(np.nan))
        for name in ('position_geometry','facing_geometry','positive'):row.setdefault('aggregate_'+name,False)
        row.setdefault('aggregate_sample_index',-1);row.setdefault('aggregate_distance_residual_m',float('nan'))
    audit['rows'].extend(rows)


@contextmanager
def observer(probe,audit):
    # Called within native launch, after original IsaacGym import.
    collector=probe.goal.source.source.support();original=collector.after
    def after(producer,pool,record):
        primary=None;before=probe.noise.on.rng()
        try:capture(probe,pool,record,audit);assert probe.noise.on.rng()==before
        except BaseException as error:primary=error
        try:result=original(producer,pool,record)
        except BaseException as error:
            if primary is None:raise
            print('Secondary original after error: '+repr(error),file=sys.stderr)
        if primary is not None:raise primary
        audit['after_calls']+=1;return result
    collector.after=after
    try:yield
    finally:collector.after=original;audit['observer_alias_restored']=collector.after is original
