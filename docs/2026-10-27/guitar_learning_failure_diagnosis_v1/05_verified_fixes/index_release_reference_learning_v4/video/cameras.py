"""Add native cameras after unchanged NN physical stepping, before collector reset."""


def pool_type(original, gymapi, np, render, GraphicsGym, finish_video, base, out, holders):
    class CapturedPool(original):
        def __init__(self,settings,folder,*args,**kwargs):
            self.video_capture, self.videos, self.video_closed = None, {}, False
            holders.append(self)
            acquire = gymapi.acquire_gym
            try:
                gymapi.acquire_gym = lambda: GraphicsGym(acquire())
                super().__init__(settings,folder,*args,**kwargs)
            finally:
                gymapi.acquire_gym = acquire
            try:
                cameras = render._create_cameras(self.scene,gymapi)
                self.scene.gym.set_camera_location(cameras['fullbody'],self.scene.envs[0],
                    gymapi.Vec3(-.10,3.4,1.1),gymapi.Vec3(-.15,-.10,.65))
                for name in cameras: self.videos[name] = render._encoder(out/(name+'.mp4'))
                self.video_capture = render._EnvZeroCapture(self,gymapi,np,cameras,self.videos)
            except BaseException:
                try: self.close()
                except BaseException: pass
                raise

        def step(self,action):
            terms = self.environment.episode_reward_terms
            previous = {k:v[0].clone() for k,v in terms.items()}
            result = super().step(action)
            before = len(self.video_capture.samples)
            reward = result[1][0].detach().cpu().numpy().copy()
            components = np.asarray([float(terms[k][0]-previous[k]) for k in terms])
            assert len(terms) == 9
            try: self.video_capture.record(before,*result[1:])
            finally:
                if len(self.video_capture.samples) > before:
                    self.video_capture.samples[-1].update(reward=reward,reward_components9=components)
            return result

        def close(self):
            errors = []
            if not self.video_closed:
                self.video_closed = True
                for name,video in self.videos.items():
                    code,issues = finish_video(video)
                    errors.extend(issues + ([] if code == 0 else [name+': encoder exit '+str(code)]))
                try:
                    capture = self.video_capture
                    if capture is not None:
                        base.save_rows(out/'native_capture.npz',capture.samples)
                        base.write(out/'capture.json',dict(
                            completed=len(capture.samples)==354 and len(capture.frame_times_s)==177 and not errors,
                            frames=len(capture.frame_times_s),controls=len(capture.samples),
                            frame_times_s=capture.frame_times_s,episode=capture.episode,
                            reward_names=list(self.environment.episode_reward_terms)))
                except BaseException as error: errors.append(repr(error))
            try: super().close()
            finally:
                if errors: base.write(out/'video_cleanup_errors.json',errors)
            if errors: raise RuntimeError(str(errors))
    return CapturedPool
