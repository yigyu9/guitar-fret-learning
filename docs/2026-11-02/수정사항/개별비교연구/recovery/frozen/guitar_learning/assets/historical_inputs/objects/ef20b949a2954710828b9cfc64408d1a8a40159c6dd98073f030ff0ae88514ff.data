"""Depth-tested six-string video overlay; no simulator mutation or new geometry."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from .strap_trial_recording import StrapTrialRecording, project
from .gym_trial_recording import GymTrialRecording, sha


def draw_strings(raw, output, endpoints, view, projection, depth):
    image=Image.open(raw).convert('RGB');width,height=image.size
    if depth.shape!=(height,width):raise ValueError('string overlay depth/image shape mismatch')
    draw=ImageDraw.Draw(image);counts=[]
    for start,end in endpoints:
        # Fixed 2049 samples cover these sub-metre strings in the native cameras.
        points=start+(end-start)*np.linspace(0,1,2049)[:,None]
        pixels,z,valid=project(points,view,projection,width,height)
        visible=np.zeros(len(points),dtype=bool);ids=np.flatnonzero(valid)
        xy=pixels[ids].astype(int)
        visible[ids]=z[ids]>=depth[xy[:,1],xy[:,0]]-.002
        for i in np.flatnonzero(visible[:-1]&visible[1:]):
            draw.line([tuple(pixels[i]),tuple(pixels[i+1])],fill=(235,235,235),width=2)
        counts.append({'visible_samples':int(visible.sum()),'occluded_samples':int((valid&~visible).sum())})
    image.save(output)
    return counts


class StringTrialRecording:
    def __init__(self,env,out):
        self.env=env;self.out=Path(out);self.strap=StrapTrialRecording(env,self.out/'strap')
        self.views=self.strap.views;self.fps=self.strap.fps;self.interval=self.strap.interval;self.frames=[]
        self.indices=[(env.guitar_bodies.index('G:string%d'%i),env.guitar_bodies.index('G:string%d_end'%i)) for i in range(1,7)]
        for view in self.views:(self.out/'frames'/view).mkdir(parents=True,exist_ok=False)

    def capture(self):
        from .environment import gymapi
        from .run_joint_hold import native_state
        from .initial_pose_noise_v1 import pose
        env=self.env;before=native_state(env);self.strap.capture()
        endpoints=np.array([[pose(before['guitar_body_states'][i])[0] for i in pair] for pair in self.indices])
        if endpoints.shape!=(6,2,3) or not np.isfinite(endpoints).all():raise AssertionError('six finite string endpoint pairs required')
        details={};images={}
        for name in self.views:
            camera=env.cameras[name];view=np.asarray(env.gym.get_camera_view_matrix(env.sim,env.env,camera));projection=np.asarray(env.gym.get_camera_proj_matrix(env.sim,env.env,camera))
            depth=np.asarray(env.gym.get_camera_image(env.sim,env.env,camera,gymapi.IMAGE_DEPTH)).reshape(720,1280)
            raw=self.strap.out/'frames'/name/('%05d.png'%len(self.frames));output=self.out/'frames'/name/raw.name
            counts=draw_strings(raw,output,endpoints,view,projection,depth)
            images[str(output)]=sha(output);details[name]={'view_matrix':view.tolist(),'projection_matrix':projection.tolist(),'strings':counts}
        if not self.frames and 'OM_appearance' in env.cameras:
            camera=env.cameras['OM_appearance'];raw=self.out/'initial_native.png';output=self.out/'initial_strings.png'
            env.gym.write_camera_image_to_file(env.sim,env.env,camera,gymapi.IMAGE_COLOR,str(raw))
            depth=np.asarray(env.gym.get_camera_image(env.sim,env.env,camera,gymapi.IMAGE_DEPTH)).reshape(960,1280)
            view=np.asarray(env.gym.get_camera_view_matrix(env.sim,env.env,camera));projection=np.asarray(env.gym.get_camera_proj_matrix(env.sim,env.env,camera))
            counts=draw_strings(raw,output,endpoints,view,projection,depth)
            details['initial_appearance']={'strings':counts,'raw_sha256':sha(raw),'output_sha256':sha(output),'view_matrix':view.tolist(),'projection_matrix':projection.tolist()}
        unchanged=native_state(env)==before
        if not unchanged:raise AssertionError('string visualization changed native state')
        self.frames.append({'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],'render_preserves_states':unchanged,'image_sha256':images,'string_endpoints_W_m':endpoints.tolist(),'cameras':details})
        data={'renderer':'Isaac Gym native cameras + strap + depth-tested six-string overlay','fps':self.fps,'string_visualization':{'physics_added':False,'pixel_width':2,'depth_tolerance_m':.002,'occluded':'hidden','scope':'actual endpoint lines, no physical string gauge/vibration'},'frames':self.frames}
        temporary=self.out/'capture.tmp';temporary.write_text(json.dumps(data,indent=2)+'\n');temporary.replace(self.out/'capture.json')

    def encode(self):
        return GymTrialRecording.encode(self)
