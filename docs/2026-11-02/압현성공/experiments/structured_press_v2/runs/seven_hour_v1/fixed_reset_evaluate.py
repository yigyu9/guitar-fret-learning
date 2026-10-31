"""B 모델을 같은 실제 초기 후보에서 비교하는 결정적 평가 진단이다.

원래 strict load와 중복 reset 보호를 유지한다. pool 생성 직전 및 strict load 직후에
명시 seed를 적용하고, 첫 post-load reset의 실제 q/유지 목표를 비교 증거로 기록한다.
"""
if __name__ == '__main__':
    import isaacgym

import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parents[1]
RUNTIME = STUDY/'runtime'
sys.path.insert(0, str(RUNTIME))


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def verify_seal():
    path = STUDY/'source_seal.json'; seal = json.loads(path.read_text())
    if len(seal['files']) != 3148 or any(not (RUNTIME/name).is_file() or digest(RUNTIME/name) != sha
                                       for name, sha in seal['files'].items()):
        raise ValueError('frozen 3148-file runtime source seal changed')
    return digest(path)


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


def run(checkpoint, out, reset_seed=4242):
    validate_seed(reset_seed)
    checkpoint, out = Path(checkpoint).resolve(), Path(out).resolve()
    if out.exists():
        raise FileExistsError('existing paired-evaluation output must not be overwritten')
    source_sha, script_sha, seal_sha = digest(checkpoint), digest(__file__), verify_seal()
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        import torch
        from guitar_learning.portability import localize
        from guitar_learning.tool.experiments import structured_press as sp
        from guitar_learning.training import finger_skill_runner as official
        payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
        official._validate_metadata_schema(payload.get('metadata'))
        official._validate_pins(payload['metadata'])
        settings = localize(payload['metadata']['settings'])
        config, source_updates = settings['structured_press'], payload['updates']
        if config['stage'] != 'B':
            raise ValueError('paired fixed-reset diagnostic currently supports saved B checkpoints only')
        del payload
        facts = dict(schema='diagnostic_fixed_reset_evaluation.v1', diagnostic_only=True,
            reset_seed=reset_seed, source_checkpoint=str(checkpoint), source_sha256=source_sha,
            source_optimizer_updates=source_updates, optimizer_updates_in_evaluation=0,
            deterministic_policy_unchanged=True, source_weights_unchanged=True,
            source_script_sha256=script_sha, source_seal_sha256=seal_sha,
            first_episode_per_env=True, failed_episodes_in_denominator=True,
            seed_sites=['immediately before original pool constructor', 'after original strict trainer.load'],
            limitations=['saved B support/physics/reward/control and duplicate-reset guard unchanged',
                'first post-load reset may reuse a zero-physics constructor reset; constructor is also seeded',
                'this does not prove earlier evaluations had different candidates; earlier assignments need actual evidence',
                'pairing requires assert_same_initial_conditions across reports, not seed equality alone',
                '32 first episodes per model; no new training or target generalization claim'])
        record = None
        try:
            with sp.structured_runtime(config):
                with fixed_reset_context(sp, official, reset_seed, config) as record:
                    report, rows = official.evaluate_checkpoint(checkpoint, out, num_envs=32,
                        scope='full_song', max_batches=1, max_episodes=32)
            if not record['strict_load_completed'] or record['initial_conditions'] is None:
                raise ValueError('strict load/first post-load reset capture missing')
            if len(rows) != 32 or {row['env_id'] for row in rows} != set(range(32)):
                raise ValueError('unique first-episode denominator env0..31 required')
            if digest(checkpoint) != source_sha or digest(__file__) != script_sha or verify_seal() != seal_sha:
                raise ValueError('source checkpoint, script or frozen runtime changed')
        except BaseException as error:
            facts.update(diagnostic_validation_failure=type(error).__name__+': '+str(error))
            raise
        finally:
            if record:
                facts.update(initial_conditions=record['initial_conditions'], reset_audit_events=record['events'],
                    original_strict_load_completed=record['strict_load_completed'],
                    cross_model_pairing_verified=False)
            path = out/'report.json'
            if path.is_file():
                saved_report = json.loads(path.read_text())
                facts['original_report_schema'] = saved_report['schema']
                saved_report.update(facts)
                if 'diagnostic_validation_failure' in facts:
                    saved_report['completed'] = False
                path.write_text(json.dumps(saved_report, ensure_ascii=False, indent=2)+'\n')
    return json.loads((out/'report.json').read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--reset-seed', type=int, default=4242)
    args = parser.parse_args()
    run(args.checkpoint, args.out, args.reset_seed)


if __name__ == '__main__':
    main()
