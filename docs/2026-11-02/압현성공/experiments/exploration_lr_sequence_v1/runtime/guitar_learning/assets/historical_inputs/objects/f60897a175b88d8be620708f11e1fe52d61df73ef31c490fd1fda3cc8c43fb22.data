"""Real Gym camera frames and MP4 encoding for an already-running trial."""
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class GymTrialRecording:
    def __init__(self,env,out):
        self.env=env;self.out=Path(out);self.frames=[];self.views=('whole_body','hands');self.fps=30
        self.interval=env.config['physics_hz']//self.fps
        if self.interval*self.fps!=env.config['physics_hz']:raise ValueError('camera rate must divide physics rate')
        for view in self.views:(self.out/'frames'/view).mkdir(parents=True,exist_ok=False)

    def capture(self):
        from .environment import gymapi,np
        from .run_joint_hold import native_state
        env=self.env;before=native_state(env);images={}
        env.gym.step_graphics(env.sim);env.gym.render_all_camera_sensors(env.sim)
        for view in self.views:
            rgba=env.gym.get_camera_image(env.sim,env.env,env.cameras[view],gymapi.IMAGE_COLOR)
            if rgba is None or np.asarray(rgba).size!=1280*720*4:raise RuntimeError('missing native camera image: '+view)
            path=self.out/'frames'/view/('%05d.png'%len(self.frames))
            env.gym.write_camera_image_to_file(env.sim,env.env,env.cameras[view],gymapi.IMAGE_COLOR,str(path))
            if not path.is_file() or not path.stat().st_size:raise RuntimeError('camera image not saved')
            images[str(path)]=sha(path)
        unchanged=native_state(env)==before
        self.frames.append({'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],'render_preserves_states':unchanged,'image_sha256':images})
        temporary=self.out/'capture.tmp'
        temporary.write_text(json.dumps({'renderer':'Isaac Gym native camera','graphics_device_id':0,'camera_config_source':'stability_adapter_2/capture_isaac_gym_initial.py',
            'fps':self.fps,'frames':self.frames},indent=2)+'\n');temporary.replace(self.out/'capture.json')
        if not unchanged:raise AssertionError('render changed native state')

    def encode(self):
        results={}
        if not self.frames:return results
        for view in self.views:
            video=self.out/(view+'.mp4')
            command=['ffmpeg','-nostdin','-n','-loglevel','error','-framerate',str(self.fps),'-i',str(self.out/'frames'/view/'%05d.png'),'-frames:v',str(len(self.frames)),'-c:v','libx264','-pix_fmt','yuv420p','-crf','20',str(video)]
            with (self.out/(view+'_encode.log')).open('w') as log:proc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
            if proc.returncode:raise RuntimeError('ffmpeg failed: '+view)
            command_probe=['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration','-of','json',str(video)]
            proc=subprocess.run(command_probe,capture_output=True,text=True)
            if proc.returncode:raise RuntimeError('ffprobe failed: '+view)
            stream=json.loads(proc.stdout)['streams'][0]
            if int(stream['nb_read_frames'])!=len(self.frames) or abs(float(stream['duration'])-len(self.frames)/self.fps)>.002:raise AssertionError('video frame/time coverage')
            results[view]={'path':str(video),'sha256':sha(video),'ffmpeg_command':command,'ffmpeg_exit_code':0,'ffprobe_command':command_probe,'ffprobe_exit_code':0,'stream':stream}
        (self.out/'videos.json').write_text(json.dumps(results,indent=2)+'\n')
        return results
