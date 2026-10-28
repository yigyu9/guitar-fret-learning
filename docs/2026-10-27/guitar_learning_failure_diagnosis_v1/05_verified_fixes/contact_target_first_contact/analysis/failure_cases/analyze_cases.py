"""Read-only selected cases; never initializes native simulation or CUDA."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import torch

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
PREVIOUS=BASE.parent/'contact_target_windup'
FOLDERS=dict(original=PREVIOUS/'run_original',delayed=PREVIOUS/'run_no_new_inward',early=BASE/'run_01')
FAILED=(7,39,43,57,102,116)
CASES=(*FAILED,8,26)


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def csvwrite(path,rows):
    with path.open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def rotate(q,v):return v+2*np.cross(q[...,:3],np.cross(q[...,:3],v)+q[...,3:4]*v)
def stats(v):
    return dict(min=float(np.min(v)),p50=float(np.median(v)),p95=float(np.quantile(v,.95)),max=float(np.max(v))) if len(v) else None


def geometry(a,selection,pins,inputs,metadata,target):
    from guitar_learning.gpu.fingertip_pad import load_fingertip_pad,pad_target_geometry
    from guitar_learning.gpu.wrong_press import pad_contact_cells
    from guitar_learning.gpu.geometry import apply,conjugate
    from guitar_learning.gpu.press_surface import project_press_strings
    from guitar_learning.gpu.rigid_guitar import _ASSET_DIR
    for module in ('fingertip_pad','wrong_press','geometry','press_surface','rigid_guitar','finger_reward'):
        path=Path('guitar_learning/gpu')/(module+'.py');path=path.resolve();assert pins[str(path)]==sha(path);inputs[str(path)]=sha(path)
    patch=load_fingertip_pad()
    for p,h in patch['contract']['source_sha256'].items():
        assert sha(Path(p))==h and pins[p]==h;inputs[p]=h
    manifest_path=(_ASSET_DIR/'manifest.json').resolve();assert pins[str(manifest_path)]==sha(manifest_path);inputs[str(manifest_path)]=sha(manifest_path)
    manifest=read(manifest_path);positions=dict(zip(manifest['logical_body_names'],manifest['logical_position_root_m']))
    indices=np.array([r for r,e in selection]);envs=np.array([e for r,e in selection]);count=len(indices)
    body=torch.tensor(a['selected_distal_pose'][indices,envs]);guitar=torch.tensor(a['guitar_pose'][indices,envs])
    world=body[:,None,:3]+apply(body[:,None,3:7],torch.tensor(patch['points_local'][1])[None])
    point=apply(conjugate(guitar[:,None,3:7]),world-guitar[:,None,:3])
    normal=apply(conjugate(guitar[:,None,3:7]),apply(body[:,None,3:7],torch.tensor(patch['normals_local'][1])[None]))
    points=torch.zeros(count,4,128,3);normals=torch.zeros_like(points);points[:,1]=point;normals[:,1]=normal
    valid=torch.zeros(4,128,dtype=torch.bool);valid[1]=True
    def local(names):
        offset=torch.tensor([positions[n] for n in names],dtype=torch.float32)
        world=guitar[:,None,:3]+apply(guitar[:,None,3:7],offset[None])
        return apply(conjugate(guitar[:,None,3:7]),world-guitar[:,None,:3])
    starts=local(['G:string%d'%n for n in range(1,7)]);ends=local(['G:string%d_end'%n for n in range(1,7)])
    frets=local(['G:nut']+['G:fret%d'%n for n in range(1,23)])
    plane=torch.tensor(metadata['press_plane_G']);loaded=torch.zeros(count,4,dtype=torch.bool)
    loaded[:,1]=torch.linalg.vector_norm(torch.tensor(a['distal_force_W'][indices,envs,2]),dim=-1)>=.01
    projected_start,projected_end=project_press_strings(starts,ends,plane)
    fret=target['fret'];low=torch.minimum(frets[:,fret-1,1],frets[:,fret,1])[:,None];high=torch.maximum(frets[:,fret-1,1],frets[:,fret,1])[:,None]
    result=pad_target_geometry(points,normals,torch.zeros_like(points),valid,projected_start,projected_end,low,high,
        torch.tensor([target['string']]),torch.tensor([target['finger']]),loaded,plane)
    qualifies,assigned,nearest=pad_contact_cells(points,normals,valid,loaded,starts,ends,frets,plane)
    records=[]
    for n,(row,env) in enumerate(selection):
        positive=bool(result['positive'][n,0]);eligible=qualifies[n,1]
        own_fret=eligible & (nearest[n,1]==target['string']) & (assigned[n,1]!=fret) & ~result['positive'][n,0]
        own_string=eligible & (nearest[n,1]!=target['string']) & ~result['positive'][n,0]
        def cells(mask):
            pairs=torch.stack((nearest[n,1][mask]+1,assigned[n,1][mask]),-1)
            return sorted(set(tuple(x) for x in pairs.tolist()))
        rawwrong=bool(a['wrong'][row,env]);own=bool(own_fret.any() or own_string.any())
        records.append(dict(env_id=env,clock=int(a['clock'][row,env]),time_s=float(a['local_time_s'][row,env]),
            recorded_candidate=bool(a['candidate'][row,env]),recorded_positive=bool(a['positive'][row,env]),recorded_wrong=rawwrong,
            reconstructed_positive=positive,positive_match=positive==bool(a['positive'][row,env]),
            position_match=bool(result['position_geometry'][n,0])==bool(a['position_geometry_any'][row,env]),
            facing_match=bool(result['facing_geometry'][n,0])==bool(a['facing_geometry_any'][row,env]),
            loaded=bool(loaded[n,1]),own_wrong_fret=bool(own_fret.any()),own_wrong_string=bool(own_string.any()),
            own_wrong_fret_cells=json.dumps(cells(own_fret)),own_wrong_string_cells=json.dumps(cells(own_string)),
            eligible_cells=json.dumps(cells(eligible)),own_cause_sufficient=rawwrong and own,unexplained_wrong=rawwrong and not own,
            other_higher_available=False))
    return records


def main():
    out=HERE/'results_v1'
    if out.exists():raise FileExistsError(str(out))
    inputs={str(Path(__file__).resolve()):sha(Path(__file__))}
    data={}
    for name,folder in FOLDERS.items():
        for filename in ('physics240.npz','target_control60.npz','evaluation.json','load_probe_report.json','inputs_before.json'):
            inputs[str((folder/filename).resolve())]=sha(folder/filename)
        with np.load(folder/'physics240.npz',allow_pickle=False) as z:a={k:z[k] for k in z.files}
        with np.load(folder/'target_control60.npz',allow_pickle=False) as z:t={k:z[k] for k in z.files}
        meta=read(folder/'load_probe_report.json')['metadata'];plane=np.asarray(meta['press_plane_G'])[:3]
        norm=rotate(a['guitar_pose'][...,3:7].astype(float),plane/np.linalg.norm(plane))
        force=a['distal_force_W'].astype(float);middle=np.linalg.norm(force[:,:,2],axis=-1);thumb=np.linalg.norm(force[:,:,0],axis=-1)
        signed=(force[:,:,2]*norm).sum(-1)
        data[name]=dict(a=a,t=t,meta=meta,middle=middle,thumb=thumb,signed=signed,episodes=read(folder/'evaluation.json')['episodes'])
    early=data['early'];a,t=early['a'],early['t'];peak_locations={}
    for window,mask in (('all_first',a['first_attempt']),('audible',a['first_attempt'] & (a['local_time_s']>=3) & (a['local_time_s']<=3.1174))):
        for body in ('middle','thumb'):
            value=np.where(mask,early[body],-np.inf);row,env=np.unravel_index(np.argmax(value),value.shape)
            peak_locations[window+'_'+body]=dict(row=int(row),env_id=int(env),clock=int(a['clock'][row,env]),time_s=float(a['local_time_s'][row,env]),N=float(value[row,env]))
    assert {v['env_id'] for v in peak_locations.values()}=={8,26}
    cases=[];timeline=[]
    for name,d in data.items():
        x,u=d['a'],d['t'];selected=[d['meta']['hand_joint_names'].index(n) for n in d['meta']['selected_joint_names']]
        for env in CASES:
            window=x['first_attempt'][:,env] & ~x['failure_latched'][:,env] & (x['local_time_s'][:,env]>=3) & (x['local_time_s'][:,env]<=3.1174)
            qerror=np.linalg.norm(x['target_LH21'][:,env,selected].astype(float)-x['actual_LH21'][:,env,selected],axis=-1)
            ep=d['episodes'][env];cm=u['first_attempt'][:,env] & ~u['post_failure'][:,env] & (u['start_clock'][:,env]>=720) & (u['start_clock'][:,env]<=748)
            armref=np.linalg.norm(u['arm_request12'][:,env].astype(float)-data['original']['t']['arm_request12'][:,env],axis=-1)
            armlate=np.linalg.norm(u['arm_request12'][:,env].astype(float)-data['delayed']['t']['arm_request12'][:,env],axis=-1)
            cases.append(dict(condition=name,env_id=env,achieved=ep['achieved'],clean_fraction=ep['clean_fraction'],wrong_fraction=ep['audible_wrong_fraction'],missing_fraction=ep['missing_fraction'],
                audible_samples=int(window.sum()),candidate_samples=int(x['candidate'][:,env][window].sum()),wrong_samples=int(x['wrong'][:,env][window].sum()),
                positive_samples=int(x['positive'][:,env][window].sum()),norm_loaded_samples=int((d['middle'][:,env][window]>=.01).sum()),
                middle_p50_N=float(np.median(d['middle'][:,env][window])),middle_max_N=float(np.max(d['middle'][:,env][window])),thumb_max_N=float(np.max(d['thumb'][:,env][window])),
                qerror_p50_deg=float(np.degrees(np.median(qerror[window]))),gate_controls=int(u['gate'][:,env][cm].sum()),audible_controls=int(cm.sum()),
                arm_original_p50_rad=float(np.median(armref[cm])),arm_delayed_p50_rad=float(np.median(armlate[cm]))))
    selection={(row,env) for env in FAILED for row in np.flatnonzero((a['local_time_s'][:,env]>=3)&(a['local_time_s'][:,env]<=3.1174))}
    for peak in (peak_locations['all_first_middle'],peak_locations['audible_middle']):
        env,center=peak['env_id'],peak['row']
        for row in range(max(0,center-8),min(len(a['clock']),center+9)):
            selection.add((row,env))
            ctrl=row//4
            for name,d in data.items():
                x,u=d['a'],d['t'];selected=[d['meta']['hand_joint_names'].index(n) for n in d['meta']['selected_joint_names']]
                qerr=x['target_LH21'][row,env,selected].astype(float)-x['actual_LH21'][row,env,selected]
                timeline.append(dict(condition=name,env_id=env,clock=int(x['clock'][row,env]),time_s=float(x['local_time_s'][row,env]),
                    middle_N=float(d['middle'][row,env]),thumb_N=float(d['thumb'][row,env]),signed_press_N=float(d['signed'][row,env]),
                    candidate=bool(x['candidate'][row,env]),wrong=bool(x['wrong'][row,env]),positive=bool(x['positive'][row,env]),
                    control_start_clock=int(u['start_clock'][ctrl,env]),gate=bool(u['gate'][ctrl,env]),precontrol_signed_N=float(u['signed_normal_force_N'][ctrl,env]),
                    fixed_Jn_old_error_m=float(u['old_normal_error_m'][ctrl,env]) if u['gate'][ctrl,env] else None,qerror_norm_deg=float(np.degrees(np.linalg.norm(qerr))),
                    arm_original_difference_rad=float(np.linalg.norm(u['arm_request12'][ctrl,env].astype(float)-data['original']['t']['arm_request12'][ctrl,env])),
                    arm_delayed_difference_rad=float(np.linalg.norm(u['arm_request12'][ctrl,env].astype(float)-data['delayed']['t']['arm_request12'][ctrl,env]))))
    selection=sorted(selection);assert len(selection)==208
    target=read(BASE/'run_01/settings.json')['song']['short_learning']['view']['source_target']
    pins=read(BASE/'run_01/inputs_before.json')
    reconstructed=geometry(a,selection,pins,inputs,early['meta'],target)
    assert not torch.cuda.is_initialized();assert all(sha(Path(p))==h for p,h in inputs.items())
    out.mkdir()
    csvwrite(out/'case_comparison.csv',cases);csvwrite(out/'peak_timeline.csv',timeline);csvwrite(out/'selected_pad_geometry.csv',reconstructed)
    write(out/'summary.json',dict(peak_locations=peak_locations,geometry_samples=len(selection),geometry_agreement={k:sum(r[k] for r in reconstructed) for k in ('positive_match','position_match','facing_match')},
        cases=cases,geometry=reconstructed,scope='selected-pad own mistake candidates only; other_higher unavailable; native body resultant not pair pressure'))
    write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_files_unchanged=True,input_sha256=inputs,geometry_sample_count=208))
    print(json.dumps(dict(completed=True,output=str(out),peak_locations=peak_locations,geometry_agreement={k:sum(r[k] for r in reconstructed) for k in ('positive_match','position_match','facing_match')})))


if __name__=='__main__':main()
