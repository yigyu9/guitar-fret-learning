"""Verify new strap overlay against preserved native frames and identical trial raw data."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'strap_video_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    output=PHASE/'verification.json';assert not output.exists()
    folder=PHASE/'native';old=BASE/'three_face_near_contact_diagnostic_v1/native/original_targets';inputs={str(p):sha(p) for p in folder.rglob('*') if p.is_file()}
    for p in [Path(__file__).resolve(),PHASE/'execution.json',PHASE/'root_preflight.json',PHASE/'previous_runner_preservation.json',PHASE/'constant_runner_preflight.json']:
        inputs[str(p)]=sha(p)
    report=read(folder/'report.json');capture=read(folder/'capture.json');rawcapture=read(folder/'raw/capture.json');init=read(folder/'initial_values.json');execution=read(PHASE/'execution.json')
    inputs.update(report['input_sha256']);assert all(sha(p)==h for p,h in inputs.items())
    from .strap_trial_recording import project
    import numpy as np
    from PIL import Image
    checks={'1200steps_5s_native_completed':report['completed'] and report['physics_steps']==1200 and report['simulation_elapsed_s']==5 and execution['exit_code']==0,'native_runtime_checks':all(report['checks'].values()),'initial_source_FK_checks':all(read(folder/'initial_grip_audit.json')['checks'].values())}
    raw_exact={};raw={}
    for n in ('states','trace','tasks','contacts','controls'):
        p=old/f'{n}.jsonl';inputs[str(p)]=sha(p);raw[n]=[json.loads(v) for v in (folder/f'{n}.jsonl').read_text().splitlines()];previous=[json.loads(v) for v in p.read_text().splitlines()];raw_exact[n]=raw[n]==previous
        checks[n+'_continuous_coverage']=len(raw[n])==(1201 if n in ('states','trace','tasks') else 1200)
    oldcap=old/'capture.json';inputs[str(oldcap)]=sha(oldcap);old_frames=read(oldcap)['frames'];frames=capture['frames'];raw_frames=rawcapture['frames'];checks['151frames_0_to5_two_views']=len(frames)==len(raw_frames)==151
    raw_images_exact=True;projected_inside=True;counts={};orange={}
    for i,frame in enumerate(frames):
        assert frame['physics_step']==i*8 and frame['time_s']==i/30 and frame['render_preserves_states'] and raw_frames[i]['render_preserves_states']
        assert frame['raw_image_sha256']==raw_frames[i]['image_sha256'] and len(frame['image_sha256'])==len(frame['raw_image_sha256'])==2
        assert frame['strap_route_points_W_m']==raw['trace'][i*8]['route_points_m'] and frame['strap_rest_length_m']==init['absolute_strap_rest_length_m']
        for view,data in frame['cameras'].items():
            p=folder/'frames'/view/f'{i:05d}.png';rp=folder/'raw/frames'/view/f'{i:05d}.png';assert sha(p)==frame['image_sha256'][str(p)] and sha(rp)==frame['raw_image_sha256'][str(rp)]
            oldsha=next(h for name,h in old_frames[i]['image_sha256'].items() if Path(name).parent.name==view);raw_images_exact &= sha(rp)==oldsha
            uv,z,valid=project(np.array(frame['strap_route_points_W_m']),np.array(data['view_matrix']),np.array(data['projection_matrix']),1280,720);projected_inside &= bool(valid.all())
            assert np.isfinite(uv).all() and (z<0).all() and data['visible_samples']>0 and data['occluded_samples']>0
            counts.setdefault(view,[]).append({k:data[k] for k in ('visible_samples','occluded_samples')})
            if i in (0,150):
                image=np.asarray(Image.open(p).convert('RGB'));assert image.shape==(720,1280,3);orange[str(p)]=int(((image[:,:,0]==255)&(image[:,:,1]==155)&(image[:,:,2]==30)).sum());assert orange[str(p)]>0
    checks['route_exact_current_trace_LA_and_read_only_render']=True;checks['image_SHA_raw_and_overlay']=True;checks['route_projects_in_both_cameras']=projected_inside;checks['visible_and_occluded_rendered_each_frame']=True
    checks['two_videos_exact_coverage']=True
    for video in report['videos'].values():
        stream=json.loads(subprocess.run(video['ffprobe_command'],capture_output=True,text=True,check=True).stdout)['streams'][0]
        assert stream==video['stream'] and stream['nb_read_frames']=='151' and stream['avg_frame_rate']=='30/1' and abs(float(stream['duration'])-151/30)<.002 and sha(video['path'])==video['sha256']
    checks['inputs_unchanged']=all(sha(p)==h for p,h in inputs.items());assert all(checks.values())
    metrics=dict(max_position_error_mm=max(t['position_error_m'] for t in raw['trace'])*1000,max_rotation_error_deg=max(t['rotation_error_deg'] for t in raw['trace']),end_position_error_mm=raw['trace'][-1]['position_error_m']*1000,end_rotation_error_deg=raw['trace'][-1]['rotation_error_deg'])
    output.write_text(json.dumps(dict(checks=checks,input_sha256=inputs,raw_arrays_exact_vs_previous=raw_exact,raw_native_images_exact_vs_previous=raw_images_exact,orange_pixel_counts=orange,sample_counts=counts,metrics=metrics,native_initializations=1,physics_steps=1200,independent_review=False,scope='root same-trial physical raw comparison is observed equality, not a success gate; actual route+native depth overlay; raw camera preserved; no extra actor/shape/state/force/cloth physics'),indent=2)+'\n')
    print(json.dumps(dict(checks=checks,raw_arrays_exact=raw_exact,raw_native_images_exact=raw_images_exact,metrics=metrics),indent=2))
if __name__=='__main__':main()
