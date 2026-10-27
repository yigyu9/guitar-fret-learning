"""CPU-only post-capture scan of the previously declared palmar facing negative."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from guitar_learning.gpu.fingertip_pad import load_fingertip_pad

HERE=Path(__file__).resolve().parent
RUN=HERE.parent/'run_01'
ROOT=HERE.parents[5]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    source=HERE.parents[1]/'negative_snapshot_audit/precommit.json'
    # The predicate was declared before this release capture; its old scope did
    # not preselect these live release outcomes or guarantee a qualifying pose.
    old=json.loads(source.read_text())
    assert 'back_facing' in old['cases']
    contract=json.loads((RUN/'training_contract.json').read_text())
    spec=contract['task']['short_learning']; target=spec['view']['source_target']
    pad=load_fingertip_pad()
    assert pad['contract']==contract['reward']['surface_learning']['pad']
    finger=target['finger']-1
    points=np.asarray(pad['points_local'],np.float32)[finger].astype(float)
    normals=np.asarray(pad['normals_local'],np.float32)[finger].astype(float)
    usable=np.asarray(pad['valid'],bool)[finger]
    path=ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json'
    rigid=json.loads(path.read_text())
    names=rigid['logical_body_names']; offsets=np.asarray(rigid['logical_position_root_m'],np.float32).astype(float)
    string=target['string']+1; fret=target['fret']
    start=offsets[names.index('G:string%d'%string)].copy()
    finish=offsets[names.index('G:string%d_end'%string)].copy()
    plane=np.asarray(contract['reward']['surface_learning']['press_surface']['plane_G'],np.float32).astype(float)
    unit=plane[:3]/np.linalg.norm(plane[:3])
    for p in (start,finish):
        p[2]=-(p[:2]@plane[:2]+plane[3])/plane[2]
    fy=[offsets[names.index('G:nut' if n==0 else 'G:fret%d'%n),1] for n in (fret-1,fret)]
    low,high=min(fy)+.002,max(fy)-.002
    line=finish-start
    a=np.load(RUN/'physics240.npz')
    first=a['first_attempt']; force=np.linalg.norm(a['distal_force_n'],axis=-1)
    rebuilt_position=np.zeros(first.shape,bool); rebuilt_facing=np.zeros_like(rebuilt_position)
    max_distance_error=0.
    # One 128-environment frame at a time, using only the captured assigned
    # distal and guitar transforms. No environment/scene or all-body replay.
    for tick in range(len(first)):
        distal,guitar=a['distal_pose'][tick],a['guitar_pose'][tick]
        rd=Rotation.from_quat(distal[:,3:7]).as_matrix()
        rg=Rotation.from_quat(guitar[:,3:7]).as_matrix()
        world=distal[:,None,:3]+np.einsum('nij,pj->npi',rd,points)
        local=np.einsum('nji,npj->npi',rg,world-guitar[:,None,:3])
        nlocal=np.einsum('nji,npj->npi',rg,np.einsum('nij,pj->npi',rd,normals))
        height=local@unit+plane[3]/np.linalg.norm(plane[:3])
        cosine=-(nlocal@unit)
        projection=np.einsum('npj,j->np',local-start,line)/(line@line)
        lateral=np.linalg.norm(local-height[...,None]*unit-start-projection[...,None]*line,axis=-1)
        position=usable&(lateral<=.003)&(local[...,1]>=low)&(local[...,1]<=high)&(height>=-.001)&(height<=.003)
        facing=position&(cosine>=.1)
        rebuilt_position[tick]=position.any(-1);rebuilt_facing[tick]=facing.any(-1)
        bounds=sorted(((low-start[1])/line[1],(high-start[1])/line[1]))
        nearest=start+np.clip(projection,max(bounds[0],0),min(bounds[1],1))[...,None]*line
        distance=np.linalg.norm(nearest-local,axis=-1);distance[:,~usable]=np.inf
        max_distance_error=max(max_distance_error,float(np.max(np.abs(distance.min(-1)-a['surface_distance_m'][tick]))))
    negative=first&(force>=.01)&rebuilt_position&~rebuilt_facing
    saved=first&(force>=.01)&a['geometry']&~a['facing']
    scopes=dict(all_first_attempt=first,
        press_to_end=first&(a['local_time_s']>=spec['view']['local_press_s'])&(a['local_time_s']<=spec['view']['local_end_s']),
        audible_onset_to_end=first&(a['local_time_s']>=spec['view']['local_onset_s'])&(a['local_time_s']<=spec['view']['local_end_s']),
        press_interval_overlap=first&(a['local_time_s']>spec['view']['local_press_s'])&(a['local_time_s']-1/240.<spec['view']['local_end_s']),
        audible_interval_overlap=first&(a['local_time_s']>spec['view']['local_onset_s'])&(a['local_time_s']-1/240.<spec['view']['local_end_s']))
    counts={}
    for name,scope in scopes.items():
        positions=np.argwhere(negative&scope)
        # Explicit deterministic (actual clock, env_id), independent of outcome.
        ordered=sorted(((int(a['clock'][t,e]),int(e),int(t)) for t,e in positions))
        first_witness=None
        if ordered:
            clock,env,t=ordered[0]
            first_witness=dict(clock=clock,env_id=env,local_time_s=float(a['local_time_s'][t,env]),
                resultant_n=float(force[t,env]),position_geometry=True,facing_geometry=False)
        counts[name]=dict(audited_samples=int(scope.sum()),matching_samples=len(ordered),first_by_clock_env=first_witness,
            recorded_flag_matching_samples=int((saved&scope).sum()))
    report=dict(schema='live_release_postcapture_facing_audit.v1',cpu_only=True,gpu_executed=False,
        selection='additional post-capture analysis of previously declared negative condition; no prespecified release outcome claim',
        declared_condition=old['cases']['back_facing'],declared_condition_source=str(source),
        order='first actual (clock,env_id); no fabricated or relaxed geometry',counts=counts,
        window_definition='press_to_end/audible_onset_to_end use endpoint timestamps within window; interval_overlap separately includes any positive original integration overlap',
        reconstructed_from='captured assigned distal/guitar poses, exact pinned palmar sample source, original rigid-guitar markers/plane',
        position_flag_mismatches=int(((rebuilt_position!=a['geometry'])&first).sum()),
        facing_flag_mismatches=int(((rebuilt_facing!=a['facing'])&first).sum()),
        negative_flag_mismatches=int((negative!=saved).sum()),maximum_distance_reconstruction_error_m=max_distance_error,
        status='available' if negative.any() else 'unavailable_in_all_declared_live_first_attempt_samples',
        limitations='No qualifying observation is absence only in this fixed task/capture. Assigned body resultant does not identify contact partners or certify dorsal contact, string pressure or sound.',
        input_sha256={str(p):sha(p) for p in [source,path,RUN/'training_contract.json',RUN/'physics240.npz',Path(__file__)]})
    assert not report['position_flag_mismatches'] and not report['facing_flag_mismatches'] and not report['negative_flag_mismatches']
    (HERE/'facing_negative_audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({key:report[key] for key in ('status','counts','maximum_distance_reconstruction_error_m')}))


if __name__=='__main__':
    main()
