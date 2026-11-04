"""새 진단에서만 초기 root 상태와 의자·기타 배치를 보정한다. 제어 법칙은 유지한다."""
import json
from pathlib import Path

import isaacgym
import torch
from isaacgym import gymapi, gymtorch
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.gpu.control import BatchedController, apply, conjugate, multiply


class NativeProxy:
    def __init__(self, native, free, chair_dz, graphics):
        self.native, self.free = native, free
        self.chair_dz, self.graphics = chair_dz, graphics
        self.loads = []
        self.simulate_calls = 0

    def __getattr__(self, name):
        return getattr(self.native, name)

    def create_sim(self, compute, graphics, engine, params):
        return self.native.create_sim(compute, compute if self.graphics else graphics, engine, params)

    def simulate(self, sim):
        self.simulate_calls += 1
        return self.native.simulate(sim)

    def load_asset(self, sim, folder, filename, options):
        human = len(self.loads) == 0
        if human:
            options.fix_base_link = not self.free
        self.loads.append(dict(path=str(Path(folder)/filename), human=human,
                               requested_fixed=bool(options.fix_base_link)))
        return self.native.load_asset(sim, folder, filename, options)

    def create_actor(self, env, asset, transform, name, *args):
        if name == 'chair':
            transform.p.z += self.chair_dz
        return self.native.create_actor(env, asset, transform, name, *args)


class MovingPelvisController(BatchedController):
    def _lower_fk(self, q):
        positions, rotations = super()._lower_fk(q)
        initial = self.initial_bodies[self.bodies.index('Pelvis')]
        actual = self.scene.snapshot()['body_state'][:, self.bodies.index('Pelvis')]
        delta = multiply(actual[:, 3:7], conjugate(initial[3:7]).expand(q.shape[0], -1))
        return (actual[:, None, :3]+apply(delta[:, None], positions-initial[:3]),
                multiply(delta[:, None], rotations))


def build(free, chair_dz=-.008, guitar_dy=0., graphics=False):
    original = gymapi.acquire_gym
    proxy = NativeProxy(original(), free, chair_dz, graphics)
    scene = None
    try:
        gymapi.acquire_gym = lambda: proxy
        try:
            scene = GpuScene(1, 'left')
        finally:
            gymapi.acquire_gym = original
        before = scene._roots[0].clone()
        desired = scene._roots[0].clone()
        desired[0, :7] = scene._prepared_bodies[0, :7]
        desired[0, 7:] = 0
        desired[1] = scene.rigid_guitar.prepared_root
        desired[1, 1] += guitar_dy
        desired[2, :7] = scene._prepared_bodies[-1, :7]
        desired[2, 2] += chair_dz
        desired[2, 7:] = 0
        # 동일 초기 경계에서만 복원한다. 동적 진행 중에는 다시 쓰지 않는다.
        torch.cuda.synchronize(scene.device)
        scene._roots[0] = desired
        torch.cuda.synchronize(scene.device)
        ids = torch.tensor([0, 1, 2], dtype=torch.int32, device=scene.device)
        if scene.gym.set_actor_root_state_tensor_indexed(scene.sim,
                gymtorch.unwrap_tensor(scene._roots), gymtorch.unwrap_tensor(ids), 3) is False:
            raise RuntimeError('Initial actor root restore rejected')
        torch.cuda.synchronize(scene.device)
        scene._refresh()
        after = scene._roots[0].clone()
        if not torch.allclose(after, desired, atol=1e-5, rtol=0):
            raise AssertionError('Native initial root readback mismatch')
        if not torch.allclose(scene.q, scene._prepared_dofs[:, 0][None], atol=1e-5, rtol=0):
            raise AssertionError('Initial joint position changed')
        if proxy.simulate_calls != 0:
            raise AssertionError('Unexpected physics during initialization')
        # 최초 snapshot도 요청한 동일 배치로 맞춘다. native 관절 FK 검증은 실제 step에서 한다.
        human = len(scene.human_bodies)
        scene._prepared_bodies[human:human+len(scene.guitar_bodies), 1] += guitar_dy
        scene._prepared_bodies[-1, 2] += chair_dz
        raw_shape = list(scene.jacobian.shape)
        expected = [1, human if free else human-1, 6, 111 if free else 105]
        if raw_shape != expected:
            raise AssertionError('Unexpected native Jacobian')
        if free:
            scene.jacobian = scene.jacobian[:, 1:, :, 6:]
        controller = MovingPelvisController(scene)
        audit = dict(before_roots13=before.cpu().tolist(), desired_roots13=desired.cpu().tolist(),
            actual_roots13=after.cpu().tolist(), native_jacobian_shape=raw_shape,
            chair_dz=chair_dz, guitar_dy=guitar_dy, asset_requests=proxy.loads,
            native_joint_velocity_max=float(scene.qd.abs().max()),
            initial_native_simulate_calls=proxy.simulate_calls,
            chair_contact_offsets=[float(p.contact_offset) for p in
                scene.gym.get_actor_rigid_shape_properties(scene.envs[0], scene.actors[0][2])],
            state_writes='initial boundary only; human root velocity zero; prepared joint state preserved')
        return scene, controller, audit
    except BaseException:
        if scene is not None:
            scene.close()
        raise


def scan(out):
    out.mkdir(exist_ok=False)
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    from guitar_learning.native.paths import pin
    from guitar_learning.training.training_log_io import active_source_paths, digest
    root = Path(__file__).resolve().parents[4]
    sources = active_source_paths(root/'guitar_learning') | prepared_input_paths() | {Path(__file__)}
    sources.update((root/'guitar_learning/assets').rglob('*.json'))
    sources.update((root/'guitar_learning/assets/gpu_rigid_guitar_v1').glob('*'))
    pins = pin(BASELINE_CONFIG, extra={p for p in sources if p.is_file()})
    (out/'inputs_before.json').write_text(json.dumps(pins, indent=2))
    cases = [(0., 0.), (-.008, 0.)]+[(-.008, dy) for dy in (.005, .01, .02, .03, .04)]
    results = []
    for index, (chair, guitar) in enumerate(cases):
        scene = None
        try:
            scene, controller, audit = build(True, chair, guitar)
            sample = scene.snapshot()
            start = scene._roots[0, 0].clone()
            rows = []
            for tick in range(3):
                target = controller.targets(torch.zeros(1, 39, device=scene.device), sample).clone()
                for _ in range(4):
                    effort = controller.efforts(sample)
                    sample = scene.step(target, effort)
                    rows.append(dict(t_s=scene.physics_steps/240.,
                        root13=scene._roots[0, 0].cpu().tolist(),
                        root_delta_m=float((scene._roots[0, 0, :3]-start[:3]).norm()),
                        contact_max_n=float(scene._native_contact_force[0, :len(scene.human_bodies)].norm(dim=-1).max()),
                        human_forces=scene._native_contact_force[0, :len(scene.human_bodies)].cpu().tolist(),
                        human_body=sample['body_state'][0, :len(scene.human_bodies)].cpu().tolist()))
            data = dict(case=index, audit=audit, rows=rows,
                        max_force_n=max(r['contact_max_n'] for r in rows),
                        max_root_m=max(r['root_delta_m'] for r in rows))
            (out/('case{:02d}.json'.format(index))).write_text(json.dumps(data, indent=2))
            summary = {k:data[k] for k in ('case','max_force_n','max_root_m')}
            summary.update(chair_dz=chair, guitar_dy=guitar)
            results.append(summary)
            print(json.dumps(results[-1]), flush=True)
        finally:
            if scene is not None:
                scene.close()
    changed = [name for name, sha in pins.items() if digest(name) != sha]
    (out/'summary.json').write_text(json.dumps(dict(completed=not changed,
        changed_inputs=changed, cases=results), indent=2))


if __name__ == '__main__':
    import sys
    scan(Path(sys.argv[1]).resolve())
