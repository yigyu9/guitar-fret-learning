"""Small real GPU PhysX/CUDA tensor probe; use via tab2body.py probe."""
import json
import isaacgym  # Must precede Torch.
from isaacgym import gymapi
import torch


def main():
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable; a working NVIDIA driver/GPU is required')
    from isaacgym import gymtorch
    gym = gymapi.acquire_gym()
    params = gymapi.SimParams()
    params.dt = 1. / 240.
    params.substeps = 1
    params.use_gpu_pipeline = True
    params.physx.use_gpu = True
    params.up_axis = gymapi.UP_AXIS_Z
    params.gravity = gymapi.Vec3(0., 0., -9.81)
    sim = gym.create_sim(0, -1, gymapi.SIM_PHYSX, params)
    if sim is None:
        raise RuntimeError('GPU PhysX simulator creation failed')
    try:
        plane = gymapi.PlaneParams()
        plane.normal = gymapi.Vec3(0., 0., 1.)
        gym.add_ground(sim, plane)
        env = gym.create_env(sim, gymapi.Vec3(-1., -1., 0.), gymapi.Vec3(1., 1., 2.), 1)
        asset = gym.create_box(sim, .1, .1, .1, gymapi.AssetOptions())
        pose = gymapi.Transform()
        pose.p = gymapi.Vec3(0., 0., 1.)
        gym.create_actor(env, asset, pose, 'probe', 0, 0)
        gym.prepare_sim(sim)
        states = gymtorch.wrap_tensor(gym.acquire_actor_root_state_tensor(sim))
        if not states.is_cuda:
            raise RuntimeError('PhysX tensor is not CUDA-backed')
        for _ in range(120):
            gym.simulate(sim)
            gym.fetch_results(sim, True)
            gym.refresh_actor_root_state_tensor(sim)
        torch.cuda.synchronize()
        if not bool(torch.isfinite(states).all()):
            raise RuntimeError('Probe produced non-finite state')
        print(json.dumps({'schema': 'tab2body.gpu_probe.v1', 'physics_steps': 120,
                          'engine': 'GPU PhysX', 'tensor_device': str(states.device),
                          'finite': True}))
    finally:
        gym.destroy_sim(sim)
    print(json.dumps({'scene_destroyed': True}))


if __name__ == '__main__':
    main()
