"""고정 reset 도구의 순수 프로토콜 함수 사본. 기존 runtime을 import하지 않는다."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_seed(seed):
    if type(seed) is not int or not 0 <= seed < 2**32:
        raise ValueError('reset seed must be an integer in [0, 2**32)')


def seed_all(seed):
    import random
    import numpy as np
    import torch
    validate_seed(seed)
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def capture_initial(pool, sp, config):
    import torch
    scene = pool.scene
    if pool.num_envs != 32 or scene.physics_steps != 0:
        raise ValueError('first post-load reset must capture 32 environments before physical stepping')
    q = scene.snapshot()['q'].detach().cpu().contiguous()
    hold = scene.initial_hold.detach().cpu().contiguous()
    if q.shape != (32, 105) or hold.shape != q.shape or not torch.isfinite(q).all() or not torch.isfinite(hold).all():
        raise ValueError('finite 32x105 actual initial q/hold required')
    arm = [scene.names.index(name) for name in sp.ACTIVE_NAMES[:12]]
    _, goal = sp.catalog_goal(config)
    candidates = [(index, row) for index, row in enumerate(goal['perturbations'])
                  if row['candidate_valid'] and row.get('native_verified', False)]
    rows = []
    for env in range(32):
        actual = q[env, arm].tolist()
        matches = [index for index, row in candidates
                   if max(abs(value-row['q105'][joint]) for value, joint in zip(actual, arm)) <= 1e-6]
        if not matches:
            raise ValueError('captured B arm state matches no verified catalog candidate')
        rows.append(dict(env_id=env, catalog_candidate_matches=matches,
            q105=q[env].tolist(), initial_hold105=hold[env].tolist(),
            q_exact_sha256=hashlib.sha256(q[env].numpy().tobytes()).hexdigest(),
            hold_exact_sha256=hashlib.sha256(hold[env].numpy().tobytes()).hexdigest()))
    return dict(environments=rows, count=32, physics_steps=0, dtype=str(q.dtype),
        sha256=canonical_sha(rows), geometry_sha256=config['geometry_sha256'], song=config['song'])


def assert_same_initial_conditions(first, second):
    """같은 seed라는 사실 대신 캡처한 환경별 실제 값의 정확한 동일성을 검사한다."""
    a, b = first['initial_conditions'], second['initial_conditions']
    if (first['reset_seed'] != second['reset_seed'] or a['geometry_sha256'] != b['geometry_sha256'] or
            a['song'] != b['song'] or a['count'] != 32 or b['count'] != 32 or
            a['environments'] != b['environments'] or a['sha256'] != b['sha256']):
        raise ValueError('paired evaluations have different actual initial conditions')
    return dict(verified=True, count=32, exact_initial_conditions_sha256=a['sha256'])


@contextmanager
def fixed_reset_context(sp, official, seed, config):
    validate_seed(seed)
    original = (sp.StructuredPool.__init__, sp.StructuredPool.reset,
                sp.StructuredTrainer.load, official._pins)
    load_was_owned = 'load' in sp.StructuredTrainer.__dict__
    record = dict(events=[], strict_load_completed=False, initial_conditions=None)
    def initialize(pool, *args, **kwargs):
        seed_all(seed)
        record['events'].append('seed_before_pool_creation')
        original[0](pool, *args, **kwargs)
    def load(trainer, *args, **kwargs):
        result = original[2](trainer, *args, **kwargs)
        record['events'].append('original_strict_load_completed')
        seed_all(seed)
        record['events'].append('seed_after_strict_load')
        record['strict_load_completed'] = True
        return result
    def reset(pool, *args, **kwargs):
        result = original[1](pool, *args, **kwargs)
        if record['strict_load_completed'] and record['initial_conditions'] is None:
            record['initial_conditions'] = capture_initial(pool, sp, config)
            record['events'].append('captured_first_postload_reset')
        return result
    def pins(settings, out, extra=()):
        return original[3](settings, out, list(extra)+[Path(__file__).resolve()])
    sp.StructuredPool.__init__, sp.StructuredPool.reset = initialize, reset
    sp.StructuredTrainer.load, official._pins = load, pins
    try:
        yield record
    finally:
        sp.StructuredPool.__init__, sp.StructuredPool.reset = original[:2]
        official._pins = original[3]
        if load_was_owned:
            sp.StructuredTrainer.load = original[2]
        else:
            delattr(sp.StructuredTrainer, 'load')
