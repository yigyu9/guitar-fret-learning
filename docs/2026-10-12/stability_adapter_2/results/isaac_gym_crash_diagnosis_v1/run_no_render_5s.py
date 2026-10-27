"""Run the selected 5s CPU PhysX candidate with no camera sensor/render during integration."""
import hashlib
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path('/home/ajou/yigyu/3')
OUT = Path(__file__).resolve().parent
REF = ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1/axis_00'
STEPS = 1200
sys.path.insert(0, str(ROOT))

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save_json(path, value):
    tmp = Path(str(path)+'.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    os.replace(tmp, path)

def contact_summary(rows):
    pairs = Counter(tuple(sorted((r['body0_name'], r['body1_name']))) for r in rows)
    raw_lambda = [float(r.get('lambda', 0.0)) for r in rows]
    return {
        'row_count': len(rows),
        'positive_raw_lambda_rows': sum(v > 0 for v in raw_lambda),
        'max_raw_lambda': max(raw_lambda, default=0.0),
        'pair_row_counts': {' | '.join(k): v for k, v in sorted(pairs.items())},
    }

class GraphicsGym:
    """Enable a graphics-capable sim, but do not create/render cameras until physics ends."""
    def __init__(self, gym):
        self.gym = gym
    def __getattr__(self, name):
        return getattr(self.gym, name)
    def create_sim(self, compute, graphics, engine, params):
        return self.gym.create_sim(compute, 0, engine, params)

from stability_adapter_2.self_collision_environment import SelfCollisionEnvironment
from stability_adapter_2.environment import gymapi
from stability_adapter_2.palm_side_feedback import context, SETTINGS
from stability_adapter_2.palm_normal_task import prepare
from stability_adapter_2.run_physx_contacts import native_state
from stability_adapter_2.run_initialization import snapshot
from stability_adapter_2.native_contacts import body_names, read_contacts
from stability_adapter_2.build_fixed_lower_asset import read as read_settings, LOWER_BODIES

class NoCameraEnvironment(SelfCollisionEnvironment):
    def __init__(self, settings, shift):
        acquire = gymapi.acquire_gym
        gymapi.acquire_gym = lambda: GraphicsGym(acquire())
        try:
            super().__init__(settings, shift)
        finally:
            gymapi.acquire_gym = acquire
    def _create_scene(self):
        super()._create_scene()
        for actor, names in ((self.human, self.human_bodies), (self.guitar, self.guitar_bodies)):
            for index, name in enumerate(names):
                rgb = (.12, .65, .3) if name.startswith('LH:') else (
                    (.8, .12, .5) if name.startswith('RH:') else
                    (.12, .3, .8) if actor == self.guitar else (.7, .7, .7))
                self.gym.set_rigid_body_color(self.env, actor, index,
                    gymapi.MESH_VISUAL_AND_COLLISION, gymapi.Vec3(*rgb))

def main():
    if any(p.exists() for p in (OUT/'run_result.json', OUT/'progress.json', OUT/'trace.jsonl')):
        raise FileExistsError('preserve prior diagnosis; use a fresh output folder')
    report_path = REF/'report.json'
    report = read(report_path)
    candidate = Path(report['candidate_path'])
    controls = read(REF/'controls.json')
    inputs = [Path(p) for p in report['source_sha256']]
    inputs += [candidate, report_path] + [REF/(n+'.json') for n in
        ('states', 'trace', 'tasks', 'contacts', 'controls')]
    input_hashes = {str(p.resolve()): sha(p) for p in inputs}
    for path, expected in report['source_sha256'].items():
        if input_hashes[str(Path(path).resolve())] != expected:
            raise AssertionError('selected reference input changed: '+path)
    if report.get('failure') or not all(report['checks'].values()) or report['physics_steps'] != 24:
        raise AssertionError('selected axis_00 reference is invalid')

    ctx = prepare(context())
    arm = ctx['indices']
    q0 = ctx['q0'][arm]
    target = np.asarray(controls[0]['final_target_rad'], dtype=np.float32)
    expected_target = q0.astype(np.float32)+np.asarray(report['bias_rad'], dtype=np.float32)
    if not np.array_equal(target, expected_target):
        raise AssertionError('saved arm target differs from selected axis_00 target')

    env = NoCameraEnvironment(read_settings(SETTINGS), ctx['shift'])
    start = time.monotonic()
    try:
        if hasattr(env, 'cameras'):
            raise AssertionError('camera collection exists before physics')
        initial = native_state(env)
        if initial != ctx['seed']:
            raise AssertionError('initial native state differs from selected seed')
        offsets = np.zeros(66, dtype=np.float32)
        for index, delta in zip(arm, target-q0.astype(np.float32)):
            offsets[list(env.main_indices).index(index)] = delta
        env.set_main_offsets(offsets)
        if not np.array_equal(env.target[arm], target):
            raise AssertionError('target application mismatch')

        names = body_names(env.gym, env.env)
        initial_sample = snapshot(env)
        trace_path = OUT/'trace.jsonl'
        contact_path = OUT/'contact_summary.jsonl'
        progress_path = OUT/'progress.json'
        samples = [initial_sample]
        save_json(OUT/'experiment.json', {
            'test': '1200-step CPU PhysX run with zero camera sensors and zero renders during physics; one camera render attempted only after physics completion',
            'requested_physics_steps': STEPS,
            'requested_duration_s': STEPS/env.config['physics_hz'],
            'physics_hz': env.config['physics_hz'], 'control_hz': env.config['control_hz'],
            'compute_device': 'CPU', 'graphics_device': 0, 'gpu_pipeline': False,
            'camera_sensors_during_physics': 0, 'camera_render_calls_during_physics': 0,
            'candidate_path': str(candidate), 'candidate_report': str(report_path),
            'initial_seed_exact': True, 'constant_arm_target_rad': target.astype(float).tolist(),
            'reference_input_sha256': input_hashes,
        })
        with trace_path.open('w') as trace_file, contact_path.open('w') as contact_file:
            trace_file.write(json.dumps({'physics_step': 0, 'sample': initial_sample}, allow_nan=False)+'\n')
            trace_file.flush()
            for _ in range(STEPS):
                env.step_physics()
                sample = snapshot(env)
                dofs = env.gym.get_actor_dof_states(env.env, env.human, gymapi.STATE_ALL)
                row = {
                    'physics_step': env.steps,
                    'time_s': env.steps/env.config['physics_hz'],
                    'sample': sample,
                    'max_abs_dof_velocity_rad_s': float(np.max(np.abs(dofs['vel']))),
                    'max_abs_dof_position_rad': float(np.max(np.abs(dofs['pos']))),
                }
                encoded = json.dumps(row, allow_nan=False)
                trace_file.write(encoded+'\n')
                trace_file.flush()
                samples.append(sample)
                if env.steps % 24 == 0 or env.steps == STEPS:
                    rows = read_contacts(env.gym, env.env, names)
                    contacts = contact_summary(rows)
                    contact_file.write(json.dumps({'physics_step': env.steps, 'time_s': env.steps/env.config['physics_hz'],
                        'contacts': contacts}, allow_nan=False)+'\n')
                    contact_file.flush()
                    os.fsync(trace_file.fileno())
                    os.fsync(contact_file.fileno())
                    progress = {
                        'status': 'physics_running', 'completed_physics_steps': env.steps,
                        'time_s': env.steps/env.config['physics_hz'], 'camera_render_calls': 0,
                        'position_error_mm': sample['position_error_m']*1000,
                        'rotation_error_deg': sample['rotation_error_deg'],
                        'guitar_linear_speed_mps': sample['linear_speed_mps'],
                        'guitar_angular_speed_rad_s': sample['angular_speed_rad_s'],
                        'strap_length_m': sample['strap_length_m'],
                        'last_applied_strap_tension_n': sample['last_applied_tension_n'],
                        'max_abs_dof_velocity_rad_s': row['max_abs_dof_velocity_rad_s'],
                        'contacts': contacts,
                    }
                    save_json(progress_path, progress)
                    print(json.dumps(progress, allow_nan=False), flush=True)
        final = native_state(env)
        fixed_names = ('Pelvis',)+LOWER_BODIES
        fixed = all(initial['human_body_states'][env.human_bodies.index(name)] ==
                    final['human_body_states'][env.human_bodies.index(name)] for name in fixed_names)
        final_contacts = read_contacts(env.gym, env.env, names)
        final_report = {
            'status': 'physics_completed', 'physics_engine': 'PhysX', 'physics_device': 'CPU',
            'gpu_pipeline': False, 'physics_steps': env.steps,
            'duration_s': env.steps/env.config['physics_hz'],
            'wall_time_s': time.monotonic()-start,
            'camera_sensors_during_physics': 0, 'camera_render_calls_during_physics': 0,
            'initial_state_matches_axis_00_seed': initial == ctx['seed'],
            'constant_arm_target_matches_saved_candidate': bool(np.array_equal(env.target[arm], target)),
            'root_and_lower_body_fixed': fixed,
            'all_1201_trace_samples_finite': len(samples) == STEPS+1 and all(s['finite'] for s in samples),
            'reference_inputs_unchanged': all(sha(Path(p)) == h for p,h in input_hashes.items()),
            'initial_sample': initial_sample, 'final_sample': samples[-1],
            'max_position_error_mm': max(s['position_error_m'] for s in samples)*1000,
            'max_rotation_error_deg': max(s['rotation_error_deg'] for s in samples),
            'final_contact_summary': contact_summary(final_contacts),
            'input_sha256': input_hashes,
        }
        if final_report['physics_steps'] != STEPS or not final_report['all_1201_trace_samples_finite']:
            raise AssertionError(final_report)
        save_json(OUT/'run_result.json', final_report)
        save_json(progress_path, {'status': 'physics_completed_camera_pending',
            'completed_physics_steps': env.steps, 'time_s': env.steps/env.config['physics_hz'],
            'camera_render_calls': 0})
        print(json.dumps({'physics_status': 'completed', 'steps': env.steps,
            'duration_s': final_report['duration_s'], 'wall_time_s': final_report['wall_time_s'],
            'max_position_error_mm': final_report['max_position_error_mm'],
            'max_rotation_error_deg': final_report['max_rotation_error_deg']}), flush=True)

        # Add and render one camera only after all physics steps are complete.
        try:
            props = gymapi.CameraProperties()
            props.width, props.height, props.horizontal_fov = 1200, 900, 45.0
            camera = env.gym.create_camera_sensor(env.env, props)
            if camera < 0:
                raise RuntimeError('camera creation after physics returned invalid handle')
            eye, look = (0.0, 3.40, 1.38), (0.0, -0.18, 0.72)
            env.gym.set_camera_location(camera, env.env, gymapi.Vec3(*eye), gymapi.Vec3(*look))
            before_render = native_state(env)
            env.gym.step_graphics(env.sim)
            env.gym.render_all_camera_sensors(env.sim)
            path = OUT/'front_fullbody_step1200.png'
            env.gym.write_camera_image_to_file(env.sim, env.env, camera, gymapi.IMAGE_COLOR, str(path))
            preserves = before_render == native_state(env)
            if not path.is_file() or path.stat().st_size < 10000:
                raise RuntimeError('camera image not written')
            camera_report = {
                'status': 'single_final_render_completed', 'physics_step': env.steps,
                'simulation_time_s': env.steps/env.config['physics_hz'],
                'camera_sensors_created_after_physics': 1,
                'camera_render_calls_during_physics': 0,
                'render_preserves_native_state': preserves,
                'image_path': str(path), 'image_sha256': sha(path),
                'camera': {'eye_world_m': eye, 'target_world_m': look,
                    'width_px': props.width, 'height_px': props.height,
                    'horizontal_fov_deg': props.horizontal_fov},
            }
            save_json(OUT/'camera_render_result.json', camera_report)
            save_json(progress_path, {'status': 'completed_physics_and_single_final_render',
                'completed_physics_steps': env.steps, 'time_s': env.steps/env.config['physics_hz'],
                'camera_render_calls_during_physics': 0, 'final_render_completed': True})
            print(json.dumps(camera_report, allow_nan=False), flush=True)
        except Exception as error:
            save_json(OUT/'camera_render_failure.json', {
                'status': 'physics_completed_camera_failed', 'physics_steps': env.steps,
                'error_type': type(error).__name__, 'error': str(error),
            })
            raise
    except Exception as error:
        save_json(OUT/'failure.json', {
            'status': 'python_exception', 'physics_steps_completed': env.steps,
            'error_type': type(error).__name__, 'error': str(error),
        })
        raise
    finally:
        env.close()

if __name__ == '__main__':
    main()
