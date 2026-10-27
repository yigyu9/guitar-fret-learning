"""Record original CPU zero-action commands for identical-force replay."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=480)
    args = parser.parse_args()
    if args.steps < 1:
        parser.error('--steps must be positive')
    import isaacgym  # Must precede imports that can load Torch.
    import numpy as np
    from scipy.spatial.transform import Rotation
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract, prepared_input_paths
    from guitar_learning.runtime.finger_session import FlexibleLeftFingerSession
    from guitar_learning.core.safety import StabilityMonitor
    from guitar_learning.native.native_contacts import body_names, read_contacts
    args.out.mkdir(parents=True, exist_ok=False)
    paths = {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    paths.update(prepared_input_paths())
    paths.add(Path(__file__).resolve())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    pins = {str(p): sha(p) for p in paths}
    write(args.out/'inputs_before.json', pins)
    contract = load_prepared_reset_contract()
    session = None
    bodies, qs, qds, targets, efforts, rows = [], [], [], [], [], []
    failure = None
    started = time.monotonic()
    try:
        (args.out/'native').mkdir()
        session = FlexibleLeftFingerSession(contract['config'], args.out/'native', physics_threads=1)
        scene = session.scene
        names = body_names(scene.gym, scene.env)
        monitor = StabilityMonitor(scene.human_bodies, scene.guitar_bodies)
        def capture():
            native = scene.native()
            bodies.append(np.asarray([[*[r['pose']['p'][a] for a in 'xyz'],
                *[r['pose']['r'][a] for a in 'xyzw'], *[r['vel']['linear'][a] for a in 'xyz'],
                *[r['vel']['angular'][a] for a in 'xyz']]
                for kind in ('human', 'guitar', 'chair') for r in native[kind+'_body_states']], dtype=np.float32)[None])
            qs.append(np.asarray([r['pos'] for r in native['human_dof_states']], dtype=np.float32)[None])
            qds.append(np.asarray([r['vel'] for r in native['human_dof_states']], dtype=np.float32)[None])
            return dict(native=native, native_contacts=dict(contacts=read_contacts(scene.gym, scene.env, names)))
        monitor.reset(capture())
        original_effort = session.controller.effort
        pending = []
        def recording_effort():
            command, diagnostic = original_effort()
            pending.append((scene.target.copy(), command.copy()))
            return command, diagnostic
        session.controller.effort = recording_effort
        g = len(scene.human_bodies)
        feet = [scene.human_bodies.index(side+'_Ankle') for side in ('L', 'R')]
        for step in range(args.steps):
            if step % 4 == 0:
                session.submit_policy_target(np.asarray(contract['target105']))
            session.integrate()
            if len(pending) != 1:
                raise RuntimeError('Expected exactly one original effort call per physics step')
            target, effort = pending.pop()
            targets.append(target)
            efforts.append(effort)
            safety = monitor.update(capture())
            body, initial = bodies[-1][0], bodies[0][0]
            distance = float(np.linalg.norm(body[g, :3]-initial[g, :3]))
            angle = float((Rotation.from_quat(initial[g, 3:7]).inv()*Rotation.from_quat(body[g, 3:7])).magnitude())
            foot = float(np.linalg.norm(body[feet, :3]-initial[feet, :3], axis=-1).max())
            speed = float(np.abs(qds[-1]).max())
            rows.append(dict(step=step+1, envs=[0], displacement_m=[distance], rotation_rad=[angle],
                foot_delta_m=[foot], speed_rad_s=[speed], failure_reasons=safety['failure_reasons'],
                pose_speed_failed=distance > .08 or angle > .35 or foot > .04 or speed > 50))
            if (step+1) % 120 == 0:
                print('original_cpu_reference', step+1, flush=True)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        if session is not None:
            session.close()
        if bodies:
            np.savez_compressed(args.out/'tape.npz', body=np.stack(bodies), q=np.stack(qs), qd=np.stack(qds),
                targets=np.asarray(targets, dtype=np.float32).reshape(-1, 105),
                efforts=np.asarray(efforts, dtype=np.float32).reshape(-1, 105))
        write(args.out/'report.json', dict(completed=failure is None, failure=failure, num_envs=1, env_ids=[0],
            requested_steps=args.steps, steps=len(rows), feedback=True, replay=None,
            scope='Original CPU controller and flexible left fingers; zero policy action; no episode reset after initialization; safety observed without adding a termination/reset',
            first_failure_physics_steps=[next((r['step'] for r in rows if r['pose_speed_failed']), -1)],
            first_native_safety_failure_step=next((r['step'] for r in rows if r['failure_reasons']), None),
            rows=rows, changed_inputs=[p for p, h in pins.items() if sha(p) != h], elapsed_s=time.monotonic()-started))


if __name__ == '__main__':
    main()
