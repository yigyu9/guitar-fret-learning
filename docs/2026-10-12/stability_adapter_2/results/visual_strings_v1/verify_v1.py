"""Check that the six-string recording changes only the displayed pixels."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
P=Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1')
N=P/'native_v1';B=P.parent/'om_body_geometry_v1/native_v2';inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    inputs[str(p)]=sha(p)
    return json.loads(Path(p).read_text())
inputs[str(Path(__file__).resolve())]=sha(__file__)
for path,h in read(P/'source_before_v1.json').items():assert sha(path)==h;inputs[path]=h
attempt=read(N/'attempt.json');verified=read(N/'inputs_verified.json')
assert verified['unchanged'] and verified['input_count']==len(attempt['input_sha256'])
for path,h in attempt['input_sha256'].items():assert sha(path)==h,path;inputs[path]=h
for name in ('trace.json','contacts.json','native_shapes.json','native_properties.json','property_cache_checks.json','initial_values.json'):
    assert read(N/name)==read(B/name),name
report=read(N/'report.json');assert report['completed'] and report['physics_steps']==1200 and report['controls']==300
assert report['music_actors']==report['checkpoint_loads']==report['policy_calls']==0 and not report['forbidden_calls']
trace=read(N/'trace.json');initial=read(N/'initial_values.json');asset=Path(initial['actual_guitar_asset']);inputs[str(asset)]=sha(asset)
nodes={b.get('name'):b for b in ET.parse(asset).findall('./worldbody/body/body')}
local=np.array([[np.fromstring(nodes[name].get('pos'),sep=' ') for name in ('G:string%d'%i,'G:string%d_end'%i)] for i in range(1,7)])
frame_count=0;max_error=0.;visible=0;occluded=0
for capture in ('media/strap/raw/capture.json','media/strap/capture.json','media/capture.json'):
    d=read(N/capture);assert len(d['frames'])==151
    for f in d['frames']:
        assert f['render_preserves_states']
        for path,h in f['image_sha256'].items():assert sha(path)==h;inputs[path]=h;frame_count+=1
        if 'string_endpoints_W_m' in f:
            ends=np.array(f['string_endpoints_W_m']);assert ends.shape==(6,2,3) and np.isfinite(ends).all()
            row=trace[f['physics_step']//4]
            expected=np.array(row['position_W_m'])+Rotation.from_quat(row['quaternion_xyzw']).apply(local.reshape(-1,3)).reshape(6,2,3)
            max_error=max(max_error,float(np.linalg.norm(ends-expected,axis=2).max()))
            for c in (f['cameras'][name] for name in ('whole_body','hands')):
                assert len(c['strings'])==6
                visible+=sum(s['visible_samples'] for s in c['strings']);occluded+=sum(s['occluded_samples'] for s in c['strings'])
assert max_error<1e-6 and visible>0 and occluded>0
for name in ('initial_native.png','initial_strings.png'):
    inputs[str(N/'media'/name)]=sha(N/'media'/name)
assert sha(N/'media/initial_native.png')!=sha(N/'media/initial_strings.png')
for video in read(N/'media/videos.json').values():
    assert video['stream']['nb_read_frames']=='151' and video['stream']['avg_frame_rate']=='30/1'
    assert video['ffmpeg_exit_code']==video['ffprobe_exit_code']==0
    assert sha(video['path'])==video['sha256'];inputs[video['path']]=video['sha256']
assert all(sha(path)==h for path,h in inputs.items())
f=P/'verification_v1.json';assert not f.exists()
f.write_text(json.dumps({'passed':True,'input_sha256':inputs,'physics_and_contacts_and_initial_and_properties_exact_to_previous':True,'native_runs':1,'physics_steps':1200,'controls':300,'frames_per_view':151,'raw_strap_and_string_frame_files':frame_count,'max_endpoint_tracking_error_m':max_error,'visible_samples':visible,'occluded_samples_hidden':occluded,'new_physics_geometry':0,'position_0_to_5_mm':trace[-1]['position_change_m']*1000,'rotation_0_to_5_deg':trace[-1]['rotation_change_deg'],'scope':'native camera recording overlay only; no string collision/mass/vibration; old physical scene preserved'},indent=2)+'\n')
print(json.dumps({'passed':True,'frame_files':frame_count,'endpoint_error_m':max_error,'physics_exact_to_previous':True}))
