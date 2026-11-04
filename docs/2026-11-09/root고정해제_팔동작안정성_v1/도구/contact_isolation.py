"""관절 구동을 끈 root 해제 장면에서 초기 접촉 충격 후보를 분리한다."""
import json
from pathlib import Path


def main(out):
    import isaacgym
    from isaacgym import gymapi, gymtorch
    import numpy as np
    import torch
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.paths import pin
    from guitar_learning.training.training_log_io import active_source_paths, digest
    root = Path(__file__).resolve().parents[4]
    out.mkdir(exist_ok=False)
    sources = active_source_paths(root/'guitar_learning') | prepared_input_paths() | {Path(__file__)}
    sources.update((root/'guitar_learning/assets').rglob('*.json'))
    sources.update((root/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*'))
    pins = pin(BASELINE_CONFIG, extra={p for p in sources if p.is_file()})
    (out/'inputs_before.json').write_text(json.dumps(pins, indent=2))
    result = []
    original = gymapi.acquire_gym
    for case in ('passive_full', 'passive_no_chair', 'passive_no_chair_guitar', 'passive_zero_gravity'):
        class Proxy:
            def __init__(self):
                self.native = original()
                self.assets = 0
            def __getattr__(self, name):
                return getattr(self.native, name)
            def load_asset(self, sim, folder, name, options):
                if self.assets == 0:
                    options.fix_base_link = False
                self.assets += 1
                return self.native.load_asset(sim, folder, name, options)
            def create_sim(self, compute, graphics, engine, params):
                if case == 'passive_zero_gravity':
                    params.gravity = gymapi.Vec3(0, 0, 0)
                return self.native.create_sim(compute, graphics, engine, params)
            def create_actor(self, env, asset, transform, name, *args):
                if name == 'chair' and case in ('passive_no_chair', 'passive_no_chair_guitar'):
                    transform.p.z -= 10.
                return self.native.create_actor(env, asset, transform, name, *args)
            def set_actor_dof_properties(self, env, actor, props):
                props['driveMode'][:] = gymapi.DOF_MODE_NONE
                props['stiffness'][:] = 0
                props['damping'][:] = 0
                return self.native.set_actor_dof_properties(env, actor, props)
        scene = None
        try:
            gymapi.acquire_gym = lambda: Proxy()
            scene = GpuScene(1, 'left')
            gymapi.acquire_gym = original
            if case == 'passive_no_chair_guitar':
                scene._roots[0, 1, 2] -= 10.
                ids = torch.tensor([1], dtype=torch.int32, device=scene.device)
                if scene.gym.set_actor_root_state_tensor_indexed(scene.sim,
                        gymtorch.unwrap_tensor(scene._roots), gymtorch.unwrap_tensor(ids), 1) is False:
                    raise RuntimeError('Initial guitar relocation rejected')
            if np.any(scene.pd_properties['driveMode'] != gymapi.DOF_MODE_NONE):
                raise AssertionError('All joint drives must be disabled')
            start = scene._roots[0, 0].clone()
            raw_initial = dict(root13=start.cpu().tolist(),
                native_body_state=scene._bodies[0].cpu().tolist(),
                q=scene.q[0].cpu().tolist(), qd=scene.qd[0].cpu().tolist(),
                jacobian_shape=list(scene.jacobian.shape),
                body_names=scene.body_names, human_bodies=scene.human_bodies)
            rows = []
            for step in range(60):
                scene.step(scene.reference105[None].clone(), torch.zeros_like(scene.efforts))
                state = scene._roots[0, 0]
                rows.append(dict(t_s=(step+1)/240., root_delta_m=float((state[:3]-start[:3]).norm()),
                    root_speed_m_s=float(state[7:10].norm()),
                    root_z_m=float(state[2]),
                    body_force_max_n=float(scene._native_contact_force[0, :len(scene.human_bodies)].norm(dim=-1).max()),
                    root13=state.cpu().tolist(),
                    human_body_forces=scene._native_contact_force[0, :len(scene.human_bodies)].cpu().tolist()))
            data = dict(case=case, completed=True, initial=raw_initial, rows=rows,
                root_max_m=max(r['root_delta_m'] for r in rows),
                speed_max_m_s=max(r['root_speed_m_s'] for r in rows),
                contact_force_max_n=max(r['body_force_max_n'] for r in rows),
                joint_drives='NONE; no commanded efforts; initial qd preserved',
                changes='only initial chair/guitar placement or global gravity, as named')
            (out/(case+'.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))
            result.append({k:data[k] for k in ('case','root_max_m','speed_max_m_s','contact_force_max_n')})
            print(json.dumps(result[-1]), flush=True)
        finally:
            gymapi.acquire_gym = original
            if scene is not None:
                scene.close()
    changed = [name for name, sha in pins.items() if digest(name) != sha]
    (out/'summary.json').write_text(json.dumps(dict(completed=not changed, changed_inputs=changed,
        cases=result, scope='initial contact isolation; not a stability or performance test'), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    import sys
    main(Path(sys.argv[1]).resolve())
