"""Static-only Isaac Gym pose editor. Physics integration and external forces are forbidden."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import time

from .capture_isaac_gym_initial import CameraEnvironment
from .environment import ROOT, gymapi, np, vector, quaternion
from .guitar_pose_edit import checked_pose, nudge, pose_delta, Rotation
from .gym_trial_recording import GymTrialRecording, sha
from .strap_trial_recording import StrapTrialRecording

BASELINE = ROOT/'docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/initial_values.json'
OUTPUT = ROOT/'docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_sessions'
HELP = 'F1/F2/F3: translate X/Y/Z | F4/F5/F6: rotate X/Y/Z | J/L: -/+\nF: fine | Tab: world/local | Z: undo | R: original guitar pose\nT: strap DISPLAY only | C: whole body/hands | G: visual/collision shapes\nS: save candidate + images | H: help | Esc: quit\nSTATIC ONLY: t=0, no gravity, collision response, PD motion or strap force.\nSpace/E do not start physics; rotation pivot is the guitar actor origin.'


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


class NoPhysicsGym:
    """Block integration and external force submission before scene creation."""
    def __init__(self, gym):
        self.gym = gym
        self.blocked_physics_calls = 0

    def create_sim(self, compute, graphics, engine, params):
        params.gravity = gymapi.Vec3(0, 0, 0)
        return self.gym.create_sim(compute, graphics, engine, params)

    def __getattr__(self, name):
        if name in ('simulate', 'fetch_results', 'apply_actor_dof_efforts',
                    'apply_body_forces', 'apply_body_force_at_pos',
                    'apply_rigid_body_force_tensors', 'apply_rigid_body_force_at_pos_tensors'):
            def forbidden(*args, **kwargs):
                self.blocked_physics_calls += 1
                raise RuntimeError('STATIC ONLY: physics API disabled: '+name)
            return forbidden
        return getattr(self.gym, name)


class StaticCameraEnvironment(CameraEnvironment):
    def __init__(self, settings, shift):
        acquire = gymapi.acquire_gym
        gymapi.acquire_gym = lambda: NoPhysicsGym(acquire())
        try:
            super().__init__(settings, shift)
        finally:
            gymapi.acquire_gym = acquire

    def step_physics(self):
        raise RuntimeError('STATIC ONLY: physics steps disabled')


class Editor:
    def __init__(self, out, candidate=None, strap=True, viewer=True):
        self.out = Path(out).resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.baseline = read(BASELINE)
        self.trial = self.baseline['input_trial']
        self.strap, self.want_viewer = strap, viewer
        self.viewer, self.env = None, None
        self.mode, self.axis, self.fine, self.local = 'EDIT', 0, False, False
        self.camera, self.collision, self.history = 0, False, []
        self.index = 0
        try:
            self.initialize(candidate)
        except BaseException:
            self.close_scene()
            raise

    def initialize(self, candidate):
        self.open_scene()
        self.reference = (self.position.copy(), self.quaternion.copy())
        if candidate is not None:
            value = read(candidate)
            if value['baseline_sha256'] != sha(BASELINE):
                raise ValueError('candidate baseline differs')
            if type(value['strap_enabled']) is not bool:
                raise ValueError('strap_enabled must be boolean')
            self.strap = value.get('strap_visible', value['strap_enabled'])
            if type(self.strap) is not bool: raise ValueError('strap_visible must be boolean')
            self.position, self.quaternion = checked_pose(value['position_W_m'], value['quaternion_xyzw'])
            self.install_pose()
        save(self.out/'session.json', {'baseline': str(BASELINE), 'baseline_sha256': sha(BASELINE),
            'candidate_input': str(Path(candidate).resolve()) if candidate else None,
            'candidate_sha256': sha(candidate) if candidate else None,
            'source_sha256': {str(Path(__file__).with_name(n)): sha(Path(__file__).with_name(n))
                for n in ('interactive_guitar_pose_static.py', 'guitar_pose_edit.py', 'GUITAR_POSE_STATIC_PLAN.md')},
            'reference_position_W_m': self.reference[0].tolist(),
            'reference_quaternion_xyzw': self.reference[1].tolist(),
            'physics_enabled': False, 'simulation_steps': 0,
            'scope': 'static visual placement only; strap display only; no integration/forces/PD motion'})
        print(HELP, flush=True)
        self.status()

    def open_scene(self):
        self.env = StaticCameraEnvironment(self.trial['initial_settings'], self.trial['guitar_initial_translation_m'])
        env = self.env
        if env.config['physics_hz'] != 240 or len(env.names) != 81 or len(env.main_indices) != 66 or len(env.leg_indices) != 0:
            raise AssertionError('240Hz, fixed lower body and 81/66 DOF layout required')
        props = env.gym.get_actor_dof_properties(env.env, env.human)
        props['stiffness'][env.torso_indices] *= 2
        props['damping'][env.torso_indices] *= np.sqrt(2)
        if not env.gym.set_actor_dof_properties(env.env, env.human, props):
            raise RuntimeError('PD property submission failed')
        env.target = np.array(self.baseline['preserved_absolute_targets_rad'], dtype=np.float32)
        if env.names != self.baseline['human_joint_names']:
            raise AssertionError('baseline joint order changed')
        env._submit_targets()
        self.initial_human = env.bodies(env.human)
        self.template = env.bodies(env.guitar)
        self.position = vector(self.template[0]['pose']['p'])
        self.quaternion = quaternion(self.template[0]['pose']['r'])
        if self.want_viewer:
            props = gymapi.CameraProperties()
            props.width, props.height = 1280, 720
            self.viewer = env.gym.create_viewer(env.sim, props)
            if self.viewer is None:
                raise RuntimeError('native viewer creation failed; run in a graphical desktop terminal')
            keys = ['F1','F2','F3','F4','F5','F6','J','L','F','TAB','Z','R','T','C','G','S','SPACE','E','H','ESCAPE']
            for key in keys:
                env.gym.subscribe_viewer_keyboard_event(self.viewer, getattr(gymapi, 'KEY_'+key), key)
            self.set_camera()

    def set_camera(self):
        p, target = (((.9,1.8,1.15),(-.06,0,.68)) if self.camera == 0 else
                     ((-.05,.72,.89),(-.105,.095,.735)))
        self.env.gym.viewer_camera_look_at(self.viewer, self.env.env, gymapi.Vec3(*p), gymapi.Vec3(*target))

    def install_pose(self):
        if self.mode != 'EDIT':
            raise RuntimeError('manual placement only allowed in EDIT')
        env = self.env
        p, q = checked_pose(self.position, self.quaternion)
        old_p = vector(self.template[0]['pose']['p'])
        old_q = quaternion(self.template[0]['pose']['r'])
        delta = Rotation.from_quat(q)*Rotation.from_quat(old_q).inv()
        states = self.template.copy()
        for state, original in zip(states, self.template):
            bp = p + delta.apply(vector(original['pose']['p'])-old_p)
            bq = (delta*Rotation.from_quat(quaternion(original['pose']['r']))).as_quat()
            for axis, value in zip('xyz', bp): state['pose']['p'][axis] = value
            for axis, value in zip('xyzw', bq): state['pose']['r'][axis] = value
        states['vel']['linear'].fill(0)
        states['vel']['angular'].fill(0)
        if not env.gym.set_actor_rigid_body_states(env.env, env.guitar, states, gymapi.STATE_ALL):
            raise RuntimeError('manual initial pose submission failed')
        actual = env.bodies(env.guitar)[0]
        self.position, self.quaternion = checked_pose(vector(actual['pose']['p']), quaternion(actual['pose']['r']))
        if np.linalg.norm(self.position-p)>1e-6 or abs(self.quaternion@q)<1-1e-6:
            raise AssertionError('native pose readback mismatch')
        if not np.array_equal(self.initial_human, env.bodies(env.human)) or env.steps != 0:
            raise AssertionError('editing changed humanoid state or advanced physics')
        env.goal_position, env.goal_quaternion = self.position.copy(), self.quaternion.copy()
        points, _ = env.route()
        env.initial_route_length = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())

    def payload(self):
        env = self.env
        return {'position_W_m': self.position.tolist(), 'quaternion_xyzw': self.quaternion.tolist(),
            'rotation_pivot': 'guitar actor root origin', 'frame': 'world, Z up',
            'baseline_path': str(BASELINE), 'baseline_sha256': sha(BASELINE),
            'delta_from_reference': pose_delta(self.position, self.quaternion, self.reference),
            'strap_enabled': False, 'strap_visible': self.strap, 'physics_enabled': False,
            'simulation_steps': 0, 'strap_rest_length_m': env.rest_length,
            'input_trial': self.trial, 'human_joint_names': env.names,
            'actual_initial_angles_rad': env.initial_q.astype(float).tolist(),
            'constant_PD_targets_rad': env.target.astype(float).tolist(),
            'body9_PD_scales': {'kp': 2., 'kd': float(np.sqrt(2))},
            'scope': 'static visual placement; strap display only; no physical interactions or stability certification'}

    def make_recorder(self, path):
        return (StrapTrialRecording if self.strap else GymTrialRecording)(self.env, path)

    def save_candidate(self):
        path = self.out/('candidate_%03d' % self.index)
        path.mkdir()
        self.index += 1
        save(path/'pose.json', self.payload())
        self.make_recorder(path/'images').capture()
        print('Saved candidate:', path/'pose.json', flush=True)
        return path


    def handle(self, key):
        if key == 'ESCAPE': return False
        if key == 'H': print(HELP, flush=True)
        elif key == 'C':
            self.camera = 1-self.camera
            if self.viewer is not None: self.set_camera()
        elif key == 'G': self.collision = not self.collision
        elif key in ('SPACE','E'): print('STATIC ONLY: physics is disabled.', flush=True)
        elif self.mode == 'EDIT':
            if key in ('F1','F2','F3','F4','F5','F6'): self.axis = int(key[1])-1
            elif key == 'F': self.fine = not self.fine
            elif key == 'TAB': self.local = not self.local
            elif key == 'T': self.strap = not self.strap
            elif key in ('J','L','R','Z'):
                if key == 'Z':
                    if not self.history: return True
                    self.position, self.quaternion = self.history.pop()
                else:
                    self.history.append((self.position.copy(), self.quaternion.copy()))
                    if key == 'R': self.position, self.quaternion = (x.copy() for x in self.reference)
                    else:
                        step = ((.0005 if self.fine else .002) if self.axis<3 else
                                np.radians(.25 if self.fine else 1.))
                        self.position, self.quaternion = nudge(self.position,self.quaternion,
                            self.axis%3, step*(-1 if key=='J' else 1), self.axis>=3, self.local)
                self.install_pose()
            elif key == 'S': self.save_candidate()
        self.status()
        return True

    def status(self):
        print('STATIC ONLY | %s %s %s | %s | %s | strap DISPLAY %s | t=%.3fs | p=%s | q(xyzw)=%s' % (
            self.mode, 'move' if self.axis<3 else 'rotate', 'XYZ'[self.axis%3],
            'local' if self.local else 'world', 'fine' if self.fine else 'normal',
            'ON' if self.strap else 'OFF', self.env.steps/240,
            np.round(self.position,6), np.round(self.quaternion,6)), flush=True)

    def draw(self):
        env = self.env
        env.gym.clear_lines(self.viewer)
        state = env.bodies(env.guitar)[0]
        p, q = vector(state['pose']['p']), quaternion(state['pose']['r'])
        directions = np.eye(3)*.07
        if self.local: directions = Rotation.from_quat(q).apply(directions)
        vertices = np.array([[p,p+d] for d in directions],dtype=np.float32)
        env.gym.add_lines(self.viewer,env.env,3,vertices,np.eye(3,dtype=np.float32))
        if self.strap:
            points,_ = env.route()
            vertices = np.stack((points[:-1],points[1:]),axis=1).astype(np.float32)
            env.gym.add_lines(self.viewer,env.env,len(vertices),vertices,
                np.tile(np.array([1.,.61,.12],dtype=np.float32),(len(vertices),1)))
        env.gym.step_graphics(env.sim)
        env.gym.draw_viewer(self.viewer,env.sim,self.collision)

    def close_scene(self):
        if self.viewer is not None:
            self.env.gym.destroy_viewer(self.viewer)
            self.viewer = None
        if self.env is not None:
            self.env.close()
            self.env = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=None)
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--no-strap',action='store_true',help='hide strap reference route; physics is always disabled')
    args = parser.parse_args()
    if not os.environ.get('DISPLAY'):
        parser.error('DISPLAY is unset. Run this tool in a graphical desktop terminal.')
    out = args.out or OUTPUT/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    editor = None
    try:
        editor = Editor(out,args.candidate,not args.no_strap)
        running = True
        while running and not editor.env.gym.query_viewer_has_closed(editor.viewer):
            start = time.monotonic()
            for event in editor.env.gym.query_viewer_action_events(editor.viewer):
                if event.value>0:
                    running = editor.handle(event.action)
                    if not running: break
            if not running: break
            editor.draw()
            time.sleep(max(0,1/30-(time.monotonic()-start)))
    finally:
        if editor is not None: editor.close_scene()


if __name__ == '__main__': main()
