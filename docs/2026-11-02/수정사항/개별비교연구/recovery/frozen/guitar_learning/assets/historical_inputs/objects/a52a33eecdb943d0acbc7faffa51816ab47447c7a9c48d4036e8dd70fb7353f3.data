"""Native Gym frames with a depth-tested overlay of the actual passive strap route."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .gym_trial_recording import GymTrialRecording, sha
FONT=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')


def project(points, view, projection, width, height):
    camera=np.column_stack((points,np.ones(len(points)))) @ view
    clip=camera @ projection
    ndc=clip[:,:2]/clip[:,3,None]
    pixels=np.column_stack(((ndc[:,0]+1)*width/2,(1-ndc[:,1])*height/2))
    valid=(camera[:,2]<-.001)&np.isfinite(pixels).all(axis=1)&(pixels[:,0]>=0)&(pixels[:,0]<width)&(pixels[:,1]>=0)&(pixels[:,1]<height)
    return pixels,camera[:,2],valid


def draw_route(raw_path, output_path, points, view, projection, depth, rest_length):
    image=Image.open(raw_path).convert('RGBA');width,height=image.size
    if depth.shape!=(height,width):raise ValueError('native depth/image shape mismatch')
    overlay=Image.new('RGBA',image.size);draw=ImageDraw.Draw(overlay);counts={'visible_samples':0,'occluded_samples':0}
    for start,end in zip(points[:-1],points[1:]):
        ends,_,_=project(np.array([start,end]),view,projection,width,height)
        count=min(4096,max(2,int(np.ceil(np.linalg.norm(ends[1]-ends[0])*2))+1))
        samples=start+(end-start)*np.linspace(0,1,count)[:,None]
        pixels,z,valid=project(samples,view,projection,width,height)
        visible=np.zeros(count,dtype=bool);ids=np.flatnonzero(valid)
        if len(ids):
            xy=pixels[ids].astype(int);scene=depth[xy[:,1],xy[:,0]]
            visible[ids]=z[ids]>=scene-.002
        counts['visible_samples']+=int(visible.sum());counts['occluded_samples']+=int((valid&~visible).sum())
        walked=np.concatenate(([0.],np.cumsum(np.linalg.norm(np.diff(pixels,axis=0),axis=1))))
        for i in range(count-1):
            if not (valid[i] and valid[i+1]):continue
            if visible[i] and visible[i+1]:color=(255,155,30,255);width_px=5
            elif int(walked[i]/8)%2==0:color=(255,190,80,100);width_px=2
            else:continue
            draw.line([tuple(pixels[i]),tuple(pixels[i+1])],fill=color,width=width_px)
    draw.rectangle((12,12,690,72),fill=(15,15,15,210));font=ImageFont.truetype(str(FONT),18)
    draw.text((23,19),f'Strap route (orange) | rest length = {rest_length:.6f} m',font=font,fill='white')
    draw.text((23,44),'Solid: visible   |   Faint dashed: behind scene geometry',font=font,fill='white')
    Image.alpha_composite(image,overlay).convert('RGB').save(output_path)
    return counts


class StrapTrialRecording:
    def __init__(self,env,out):
        self.env=env;self.out=Path(out);self.raw=GymTrialRecording(env,self.out/'raw');self.views=self.raw.views;self.fps=self.raw.fps;self.interval=self.raw.interval;self.frames=[]
        for view in self.views:(self.out/'frames'/view).mkdir(parents=True,exist_ok=False)

    def capture(self):
        from .environment import gymapi
        from .run_joint_hold import native_state
        before=native_state(self.env);self.raw.capture();points,_=self.env.route();details={};images={};env=self.env
        if points.shape!=(13,3) or not np.isfinite(points).all():raise AssertionError('current passive strap must have13 finite route points')
        for name in self.views:
            camera=env.cameras[name];view=np.asarray(env.gym.get_camera_view_matrix(env.sim,env.env,camera));projection=np.asarray(env.gym.get_camera_proj_matrix(env.sim,env.env,camera))
            depth=np.asarray(env.gym.get_camera_image(env.sim,env.env,camera,gymapi.IMAGE_DEPTH)).reshape(720,1280)
            raw=self.out/'raw/frames'/name/('%05d.png'%len(self.frames));output=self.out/'frames'/name/raw.name
            stats=draw_route(raw,output,points,view,projection,depth,env.rest_length)
            images[str(output)]=sha(output);details[name]=dict(view_matrix=view.tolist(),projection_matrix=projection.tolist(),**stats)
        unchanged=native_state(env)==before
        self.frames.append(dict(physics_step=env.steps,time_s=env.steps/env.config['physics_hz'],render_preserves_states=unchanged,image_sha256=images,raw_image_sha256=self.raw.frames[-1]['image_sha256'],strap_route_points_W_m=points.tolist(),strap_rest_length_m=env.rest_length,cameras=details))
        temporary=self.out/'capture.tmp';temporary.write_text(json.dumps(dict(renderer='Isaac Gym native camera + actual strap-route overlay',camera_config_source='stability_adapter_2/capture_isaac_gym_initial.py',fps=self.fps,strap_visualization=dict(visible='orange solid',occluded='faint dashed',depth_tolerance_m=.002,font_path=str(FONT),font_sha256=sha(FONT),scope='actual routed cable path; no cloth thickness/sag or additional physics'),frames=self.frames),indent=2)+'\n');temporary.replace(self.out/'capture.json')
        if not unchanged:raise AssertionError('strap rendering/query changed human or guitar state')

    def encode(self):
        return GymTrialRecording.encode(self)
