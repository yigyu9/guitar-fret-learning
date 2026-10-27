"""Verify the preserved source geometry and two native diagnostic records."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation

R = Path('/home/ajou/yigyu/3')
A = R/'stability_adapter_2'
P = R/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1'

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

inputs = {str(Path(__file__).resolve()): sha(__file__)}
def pinned(p):
    inputs[str(p)] = sha(p)
    return read(p)

depth = pinned(P/'depth_v1.json')
builds = [pinned(P/f'build_v{i}.json') for i in (1,2,3)]
for b in builds:
    assert all(b['checks'].values())
    for path,value in b['input_sha256'].items():
        assert sha(path)==value,path
        inputs[path]=value
    assert sha(b['asset'])==b['asset_sha256']
    inputs[b['asset']]=b['asset_sha256']
    for m in b['meshes']:
        assert sha(m['path'])==m['sha256']
        inputs[m['path']]=m['sha256']
for filename in ['body_visual.obj']+[f'body_collision_{i:02d}.obj' for i in range(63)]:
    hashes=[sha(A/f'assets/om_body_geometry_v{i}'/filename) for i in (1,2,3)]
    assert len(set(hashes))==1,filename
    for i,h in zip((1,2,3),hashes): inputs[str(A/f'assets/om_body_geometry_v{i}'/filename)]=h
mesh=A/'assets/om_body_geometry_v3/body_visual.obj'
v=np.array([[float(x) for x in line.split()[1:4]] for line in mesh.read_text().splitlines() if line.startswith('v ')])
fc=np.array(depth['arcs']['front']['center_DXF_mm'])/1000
bc=np.array(depth['arcs']['back']['center_DXF_mm'])/1000
rf=depth['arcs']['front']['radius_mm']/1000;rb=depth['arcs']['back']['radius_mm']/1000
sx0,sx1=np.array(depth['side_axis_interval_mm'])/1000
sx=sx0+(sx1-sx0)*(v[:,1]-v[:,1].min())/np.ptp(v[:,1])
anchor=.02-(fc[1]+rf)
front=anchor+fc[1]+np.sqrt(rf*rf-(sx-fc[0])**2-v[:,0]**2)
back=anchor+bc[1]-np.sqrt(rb*rb-(sx-bc[0])**2-v[:,0]**2)
surface_error=float(np.minimum(abs(v[:,2]-front),abs(v[:,2]-back)).max())
assert surface_error<1e-7
reference=pinned(P.parent/'realistic_guitar_proportions_v1/native_realistic_v2/native_properties.json')
old_initial=pinned(P.parent/'realistic_guitar_proportions_v1/native_realistic_v2/initial_values.json')
metrics={}
for version in (1,2):
    n=P/f'native_v{version}'
    attempt=pinned(n/'attempt.json');verified=pinned(n/'inputs_verified.json')
    assert verified['unchanged'] and verified['input_count']==len(attempt['input_sha256'])
    for path,value in attempt['input_sha256'].items():
        assert sha(path)==value,path
        inputs[path]=value
    report=pinned(n/'report.json');props=pinned(n/'native_properties.json')
    trace=pinned(n/'trace.json');contacts=pinned(n/'contacts.json');initial=pinned(n/'initial_values.json')
    shapes=pinned(n/'native_shapes.json');cache=pinned(n/'property_cache_checks.json')
    assert report['completed'] and report['physics_steps']==1200 and report['controls']==300
    assert not report['forbidden_calls'] and report['music_actors']==report['policy_calls']==report['checkpoint_loads']==0
    assert props['setter_calls_before_initialization']==1 and props['property_setter_rejections']==0 and all(cache.values())
    assert shapes['shape_count']==91 and len(shapes['body_names'])==39
    assert shapes['shape_ranges'][shapes['body_names'].index('G:body')][1]==63
    assert len(trace)==301 and len(contacts)==300
    assert initial['source_audit']['source_clear']
    for imported,requested,applied,old in zip(props['imported'],props['requested'],props['applied'],reference['applied']):
        assert imported['name']==requested['name']==applied['name']==old['name']
        assert applied['mass_kg']==old['mass_kg']
        assert imported['COM_body_m']==requested['COM_body_m']==applied['COM_body_m']
        target=np.asarray(imported['inertia_COM_kg_m2'])*(old['mass_kg']/imported['mass_kg'])
        assert np.allclose(requested['inertia_COM_kg_m2'],target,rtol=1e-5,atol=1e-9)
        assert np.allclose(applied['inertia_COM_kg_m2'],requested['inertia_COM_kg_m2'],rtol=1e-5,atol=1e-9)
        assert np.linalg.eigvalsh(applied['inertia_COM_kg_m2']).min()>0
    q=np.asarray(initial['q_ref_rad']);oldq=np.asarray(old_initial['q_ref_rad']);names=initial['joint_names']
    changed=[names[i] for i in np.flatnonzero(q!=oldq)]
    assert all(n.startswith('R_') and any(s in n for s in ('Thorax','Shoulder','Elbow','Wrist')) for n in changed)
    assert max(abs(q-oldq))<=.15
    assert all(np.array_equal(row['submitted_target_rad'],q) for row in trace)
    frames=0
    for cap in ('media/raw/capture.json','media/capture.json'):
        capture=pinned(n/cap)
        assert len(capture['frames'])==151
        for f in capture['frames']:
            assert f['render_preserves_states']
            for path,value in f['image_sha256'].items():
                assert sha(path)==value
                inputs[path]=value;frames+=1
    videos=pinned(n/'media/videos.json')
    for video in videos.values():
        assert video['ffmpeg_exit_code']==video['ffprobe_exit_code']==0
        assert video['stream']['nb_read_frames']=='151' and video['stream']['avg_frame_rate']=='30/1'
        assert sha(video['path'])==video['sha256'];inputs[video['path']]=video['sha256']
    start,two,end=trace[0],trace[120],trace[-1]
    d=float(np.linalg.norm(np.array(end['position_W_m'])-two['position_W_m']))
    rot=float(np.rad2deg((Rotation.from_quat(two['quaternion_xyzw']).inv()*Rotation.from_quat(end['quaternion_xyzw'])).magnitude()))
    metrics[f'native_v{version}']={'position_0_to_5_mm':end['position_change_m']*1000,'rotation_0_to_5_deg':end['rotation_change_deg'],'position_2_to_5_mm':d*1000,'rotation_2_to_5_deg':rot,'right_arm_initial_max_change_rad':float(max(abs(q-oldq))),'changed_joint_names':changed,'total_mass_kg':props['total_mass_kg'],'strap_rest_length_m':initial['strap_initial']['rest_length_m'],'frame_files':frames,'contact_observation_samples':len(contacts),'contact_sample_timing':'before each control, steps0..1196; raw lambda is not calibrated N'}
traces=[read(P/f'native_v{i}/trace.json') for i in (1,2)]
max_diff=max(float(np.linalg.norm(np.array(a['position_W_m'])-b['position_W_m'])) for a,b in zip(*traces))
assert all(sha(path)==value for path,value in inputs.items())
out={'passed':True,'input_sha256':inputs,'mesh_surface_max_error_m':surface_error,'body_dimensions_m':np.ptp(v,axis=0).tolist(),'body_bbox_z_span_is_not_local_depth':True,'geometry_checks':builds[-1]['checks'],'collision_XY_sampled_only':True,'metrics':metrics,'native_v1_v2_max_actor_position_difference_m':max_diff,'stabilization_success_claim':False}
file=P/'verification_v1.json';assert not file.exists();file.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='input_sha256'},ensure_ascii=False,indent=2))
