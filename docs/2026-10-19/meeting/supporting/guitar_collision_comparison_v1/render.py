"""Native visual/collision camera comparison; no physics steps or asset edits."""
from isaacgym import gymapi
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MEETING = HERE.parent.parent
ROOT = MEETING.parents[2]
OUT = MEETING/'result/images/guitar_collision_comparison_v1'
OUT.mkdir(exist_ok=False)
ASSET = ROOT/'stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml'
REF = ROOT/'docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/native_hold_v4/media/actual_shape_properties.json'
MANIFEST = ASSET.parent/'manifest.json'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
xml = ET.parse(ASSET).getroot()
meshdir = ASSET.parent/xml.find('compiler').get('meshdir','.')
paths = {Path(__file__).resolve(),ASSET,REF,MANIFEST}
paths.update((meshdir/m.attrib['file']).resolve() for m in xml.findall('./asset/mesh'))
before = {str(p):sha(p) for p in sorted(paths)}
(HERE/'inputs_before.json').write_text(json.dumps(before,indent=2)+'\n')
reference = json.loads(REF.read_text())['guitar']
gym = gymapi.acquire_gym()
params = gymapi.SimParams()
params.up_axis = gymapi.UP_AXIS_Z
params.use_gpu_pipeline = False
params.physx.use_gpu = False
params.physx.num_threads = 1
sim = gym.create_sim(0,0,gymapi.SIM_PHYSX,params)
assert sim is not None
try:
    env = gym.create_env(sim,gymapi.Vec3(-2,-2,0),gymapi.Vec3(2,2,2),1)
    options = gymapi.AssetOptions()
    options.fix_base_link = True
    options.disable_gravity = True
    options.collapse_fixed_joints = False
    asset = gym.load_asset(sim,str(ASSET.parent),ASSET.name,options)
    assert asset is not None
    pose = gymapi.Transform()
    pose.p = gymapi.Vec3(0,0,.95)
    pose.r = gymapi.Quat.from_axis_angle(gymapi.Vec3(1,0,0),math.pi/2)
    actor = gym.create_actor(env,asset,pose,'current_OM',0,0,1)
    names = gym.get_actor_rigid_body_names(env,actor)
    ranges = gym.get_actor_rigid_body_shape_indices(env,actor)
    props = gym.get_actor_rigid_shape_properties(env,actor)
    body_id = names.index('G:body')+1
    assert ranges[names.index('G:body')].count == 63
    shapes = {}
    for i,(name,indices) in enumerate(zip(names,ranges)):
        gym.set_rigid_body_segmentation_id(env,actor,i,i+1)
        imported = props[indices.start:indices.start+indices.count]
        expected = reference[name]
        assert len(imported) == len(expected),(name,len(imported),len(expected))
        for prop,ref in zip(imported,expected):
            prop.filter = ref['filter']
            prop.contact_offset = ref['contact_offset_m']
            prop.rest_offset = ref['rest_offset_m']
            prop.friction = ref['friction']
        shapes[name] = {'segmentation_id':i+1,'start':indices.start,'count':indices.count,
                        'filter': [int(p.filter) for p in imported],
                        'contact_offset_m':[float(p.contact_offset) for p in imported],
                        'rest_offset_m':[float(p.rest_offset) for p in imported]}
    gym.set_actor_rigid_shape_properties(env,actor,props)
    readback = gym.get_actor_rigid_shape_properties(env,actor)
    for a,b in zip(props,readback):
        assert a.filter==b.filter and abs(a.contact_offset-b.contact_offset)<1e-9
    gym.set_light_parameters(sim,0,gymapi.Vec3(.65,.65,.65),
                             gymapi.Vec3(.35,.35,.35),gymapi.Vec3(-.3,-.6,-1))
    views = [('whole_front',[0,-2.05,.8],[0,0,.8],40),
             ('body_front',[0,-.95,.55],[0,0,.55],36),
             ('body_side',[.85,0,.55],[0,0,.55],36)]
    cameras = []
    for name,eye,target,fov in views:
        for kind in ['visual','collision']:
            cp = gymapi.CameraProperties()
            cp.width,cp.height,cp.horizontal_fov=1000,1000,fov
            cp.use_collision_geometry = kind=='collision'
            camera = gym.create_camera_sensor(env,cp)
            assert camera>=0
            gym.set_camera_location(camera,env,gymapi.Vec3(*eye),gymapi.Vec3(*target))
            cameras.append((name,kind,camera,eye,target,fov))
    gym.prepare_sim(sim)
    gym.step_graphics(sim)
    gym.render_all_camera_sensors(sim)
    arrays = {}
    outputs = []
    for name,kind,camera,eye,target,fov in cameras:
        prefix = name+'_'+kind
        rgba = np.asarray(gym.get_camera_image(sim,env,camera,gymapi.IMAGE_COLOR)).reshape(1000,1000,4)
        seg = np.asarray(gym.get_camera_image(sim,env,camera,gymapi.IMAGE_SEGMENTATION)).reshape(1000,1000)
        depth = np.asarray(gym.get_camera_image(sim,env,camera,gymapi.IMAGE_DEPTH)).reshape(1000,1000)
        assert (seg==body_id).sum()>1000,(prefix,np.unique(seg),int((seg==body_id).sum()))
        path = OUT/(prefix+'.png')
        Image.fromarray(rgba[:,:,:3],'RGB').save(path)
        arrays[prefix+'_seg']=seg.copy()
        arrays[prefix+'_depth']=depth.copy()
        outputs.append({'file':str(path),'sha256':sha(path),'view':name,'kind':kind,
                        'eye_m':eye,'target_m':target,'fov_deg':fov,
                        'body_pixels':int((seg==body_id).sum())})
    np.savez_compressed(HERE/'native_arrays.npz',**arrays)
    after = {str(p):sha(p) for p in sorted(paths)}
    assert before==after
    report = {'renderer':'Isaac Gym native cameras; use_collision_geometry false/true',
              'physics_steps':0,'asset':str(ASSET),'asset_options':{'fixed_base':True,'gravity_disabled':True},
              'actor_position_m':[0,0,.95],'actor_quaternion_xyzw':[pose.r.x,pose.r.y,pose.r.z,pose.r.w],
              'body_id':body_id,'shape_reference':str(REF),'shape_properties':shapes,
              'excluded_runtime_bodies':['G:thumb_support_proxy','G:pluck_range'],
              'inputs_unchanged':before==after,'input_sha256':before,'images':outputs,
              'scope':'Imported collision geometry rendering; excludes contact-offset inflation, forces and dynamic stability certification'}
    (HERE/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'body_collision_shapes':63,'saved_images':len(outputs),'inputs_unchanged':True}),flush=True)
finally:
    gym.destroy_sim(sim)
