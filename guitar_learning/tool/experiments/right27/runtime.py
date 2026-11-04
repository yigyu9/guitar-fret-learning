"""봉인된 공용 소스를 바꾸지 않고 이번 프로세스에서만 오른손27 경로를 연결한다."""
from contextlib import contextmanager


@contextmanager
def right27_runtime():
    # 호출자가 isaacgym을 먼저 import한 뒤 들어와야 한다.
    from guitar_learning.training import rollout, policy
    from .pool import Right27Pool
    from .policy import Right27Policy
    old_pool, old_policy = rollout.GpuPool, policy.SpecialistPolicy
    rollout.GpuPool, policy.SpecialistPolicy = Right27Pool, Right27Policy
    try:
        yield
    finally:
        rollout.GpuPool, policy.SpecialistPolicy = old_pool, old_policy


def settings_for(args):
    from guitar_learning.training.launch import build_settings
    options = dict(learning_family='song', updates=args.updates, num_envs=args.num_envs,
                   horizon=args.horizon, size=args.size, seed=args.seed, physics='gpu')
    if args.song is not None:
        options['song'] = args.song
    settings = build_settings('right', **options)
    settings['right27'] = dict(schema='guitar_learning.right27.v1', active_dimensions=27,
                               fingers=21, elbow_wrist=6)
    return settings


def train(settings, out, resume=None):
    from types import SimpleNamespace
    from guitar_learning.tool.training.legacy_gpu_runner import run
    with right27_runtime():
        return run(settings, SimpleNamespace(out=out, resume=resume))
