"""원본 strict 평가의 60Hz 보상만 읽는다. GPU 실행은 CLI를 명시 실행할 때만 한다."""
import argparse
from contextlib import contextmanager, nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parents[1]
PROTOCOL = ROOT/'variance_variant/runtime/guitar_learning/tool/experiments/variance_reset_protocol.py'
TERMS = ('song_left_approach', 'song_left_contact', 'song_clean_hold', 'song_left_success',
         'song_wrong_press', 'song_performance_deficit', 'song_finger_standby', 'song_thumb_support', 'action_change')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seal(runtime, path):
    files = json.loads(path.read_text())['files']
    if any(digest(runtime/name) != sha for name, sha in files.items()):
        raise ValueError('sealed source changed')
    return digest(path)


@contextmanager
def trace_context(sp, official, seed_all, seed):
    """원본 반환 tensor를 그대로 돌려주고 첫 episode의 최종9항만 복사한다."""
    import torch
    original = (sp.StructuredPool.__init__, sp.StructuredPool.reset,
                sp.StructuredTrainer.load, sp.StructuredEnvironment._reward_components, official._pins)
    owned = ('load' in sp.StructuredTrainer.__dict__, '_reward_components' in sp.StructuredEnvironment.__dict__)
    record = dict(armed=False, rows=[], seen=set(), last_tick={}, initial=None)
    def initialize(pool, *args, **kwargs):
        seed_all(seed)
        original[0](pool, *args, **kwargs)
    def load(trainer, *args, **kwargs):
        result = original[2](trainer, *args, **kwargs)
        record.update(armed=True, trainer=trainer, initial_updates=trainer.updates,
            model_before={k:v.detach().cpu().clone() for k,v in trainer.policy.state_dict().items()})
        seed_all(seed)
        return result
    def reset(pool, *args, **kwargs):
        result = original[1](pool, *args, **kwargs)
        if record['armed'] and record['initial'] is None:
            if pool.num_envs != 32 or pool.scene.physics_steps != 0:
                raise ValueError('32 initial environments before physical stepping required')
            record['initial'] = dict(q105=pool.scene.snapshot()['q'].detach().cpu().clone(),
                hold105=pool.scene.initial_hold.detach().cpu().clone())
            for value in record['initial'].values():
                if value.shape != (32, 105) or not torch.isfinite(value).all():
                    raise ValueError('finite actual q/hold32x105 required')
        return result
    def components(env, legacy):
        values = original[3](env, legacy)
        if record['armed']:
            if record['initial'] is None or tuple(values) != TERMS:
                raise ValueError('initial reset or nine-term contract missing')
            for i in range(env.N):
                if i in record['seen']:
                    continue
                # native end_control은 steps를 먼저 증가시키므로 trace만 0기반으로 정규화한다.
                tick = int(env.steps[i])-1
                if tick != record['last_tick'].get(i, -1)+1:
                    raise ValueError('duplicate or missing first-episode tick')
                record['last_tick'][i] = tick
                terminal = bool(env.invalid[i] or env._local_time()[i]+1e-9 >= env._episode_duration()[i])
                record['rows'].append(dict(env=i, tick=tick,
                    terms=torch.stack([values[k][i] for k in TERMS]).detach().cpu().clone(),
                    cost=float(env.tick_cost[i]), phi_before=float(env.before_surface_potential[i]),
                    local_time=float(env._local_time()[i]), terminal=terminal,
                    gamma=float(env.approach_gamma)))
                if terminal:
                    record['seen'].add(i)
        return values
    def pins(settings, out, extra=()):
        return original[4](settings, out, list(extra)+[Path(__file__).resolve(), PROTOCOL])
    sp.StructuredPool.__init__, sp.StructuredPool.reset = initialize, reset
    sp.StructuredTrainer.load, sp.StructuredEnvironment._reward_components, official._pins = load, components, pins
    try:
        yield record
    finally:
        sp.StructuredPool.__init__, sp.StructuredPool.reset, official._pins = original[0], original[1], original[4]
        for cls, name, had, value in ((sp.StructuredTrainer, 'load', owned[0], original[2]),
                (sp.StructuredEnvironment, '_reward_components', owned[1], original[3])):
            if had:
                setattr(cls, name, value)
            else:
                delattr(cls, name)


def reconcile(rows, episodes, *, reward_gamma, cost_gamma):
    """실패 포함 최초32개 원시 episode와 trace 합·할인합을 대조한다."""
    import numpy as np
    if len(episodes) != 32 or {e['env_id'] for e in episodes} != set(range(32)):
        raise ValueError('native first32 denominator required')
    result = []
    for episode in episodes:
        values = [x for x in rows if x['env'] == episode['env_id']]
        if not values or len(values) != episode['steps'] or not values[-1]['terminal']:
            raise ValueError('incomplete first episode trace')
        terms = np.stack([x['terms'].numpy() for x in values]).astype(float)
        costs = np.array([x['cost'] for x in values]); gamma = reward_gamma
        if any(x['gamma'] != reward_gamma for x in values):
            raise ValueError('approach gamma differs from reward gamma')
        expected = np.array([episode['reward_components'][k] for k in TERMS])
        error = max(float(abs(terms.sum(0)-expected).max()), abs(costs.sum()-episode['cost']),
                    abs(terms.sum()-episode['reward']))
        if error > 2e-5:
            raise ValueError('native raw totals do not reconcile: '+str(error))
        discount = gamma**np.arange(len(values))
        result.append(dict(env_id=episode['env_id'], ticks=len(values), max_reconciliation_error=error,
            discounted_terms=dict(zip(TERMS, (terms*discount[:, None]).sum(0).tolist())),
            undiscounted_terms=dict(zip(TERMS, terms.sum(0).tolist())),
            discounted_cost=float(costs@(cost_gamma**np.arange(len(values)))), phi_initial=values[0]['phi_before'],
            discounted_shaping_terminal_zero_residual=float(terms[:, 0]@discount+values[0]['phi_before'])))
    return result


def _run(checkpoint, out, variant):
    import torch
    import numpy as np
    runtime = STUDY/'runtime' if variant == 'base' else ROOT/'no_alignment_prior_variant/runtime'
    seal_path = STUDY/'source_seal.json' if variant == 'base' else runtime.parent/'source_seal.json'
    if out.exists():
        raise FileExistsError(str(out))
    before = seal(runtime, seal_path)
    pins = {str(p):digest(p) for p in (checkpoint, Path(__file__), PROTOCOL)}
    spec = importlib.util.spec_from_file_location('reward_trace_reset_protocol', PROTOCOL)
    protocol = importlib.util.module_from_spec(spec); spec.loader.exec_module(protocol)
    from guitar_learning.portability import localize
    from guitar_learning.tool.experiments import structured_press as sp
    from guitar_learning.training import finger_skill_runner as official
    if Path(sp.__file__).resolve() != runtime/'guitar_learning/tool/experiments/structured_press.py':
        raise ValueError('incorrect runtime imported')
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    official._validate_metadata_schema(payload['metadata']); official._validate_pins(payload['metadata'])
    settings = localize(payload['metadata']['settings']); config = settings['structured_press']
    if config['stage'] != 'free_v9':
        raise ValueError('exact saved free_v9 checkpoints only; export A before this probe')
    context = nullcontext()
    if variant == 'no_prior':
        from guitar_learning.tool.experiments.no_alignment_prior import no_prior_context, verify
        verify(); context = no_prior_context()
    out.mkdir(parents=True)
    summary = dict(completed=False, variant=variant, reset_seed=4242, checkpoint_sha256=pins[str(checkpoint)],
        source_runtime=str(runtime), source_seal_sha256=before,
        source_config_sha256=hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
        reward_gamma=settings['ppo']['gamma'], cost_gamma=settings['ppo']['cost_gamma'],
        diagnostic_only=True, changes='read-only recording; deterministic reset seed',
        phi_after='not independently read: no extra geometry calls; before potential and measured shaping recorded')
    try:
        with context, sp.structured_runtime(config):
            with trace_context(sp, official, protocol.seed_all, 4242) as record:
                report, episodes = official.evaluate_checkpoint(checkpoint, out/'native', num_envs=32,
                    scope='full_song', max_batches=1, max_episodes=32)
        if not record['armed'] or record['seen'] != set(range(32)) or record['initial'] is None:
            raise ValueError('strict load/reset/terminal trace missing')
        trainer = record['trainer']
        if set(record['model_before']) != set(payload['model']) or any(
                not torch.equal(v, payload['model'][k]) for k,v in record['model_before'].items()):
            raise ValueError('actual loaded model differs from saved source')
        unchanged = all(torch.equal(v, trainer.policy.state_dict()[k].detach().cpu()) for k,v in record['model_before'].items())
        if not unchanged or trainer.updates != record['initial_updates'] or trainer.updates != payload['updates']:
            raise ValueError('evaluation changed weights or optimizer updates')
        if not report['completed'] or report.get('lifecycle_verified') is not True or any(
                report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors')):
            raise ValueError('native lifecycle/integrity incomplete')
        reconciled = reconcile(record['rows'], episodes, reward_gamma=settings['ppo']['gamma'],
            cost_gamma=settings['ppo']['cost_gamma'])
        if any(abs(x['discounted_shaping_terminal_zero_residual']) > 2e-5 for x in reconciled):
            raise ValueError('discounted shaping does not telescope')
        if variant == 'no_prior':
            verify()
        if seal(runtime, seal_path) != before or any(digest(Path(p)) != h for p,h in pins.items()):
            raise ValueError('checkpoint/helper/source changed')
        initial = {k:v.numpy() for k,v in record['initial'].items()}
        np.savez_compressed(out/'initial.npz', **initial)
        rows = record['rows']
        np.savez_compressed(out/'trace.npz', terms=np.stack([x['terms'].numpy() for x in rows]),
            **{k:np.array([x[k] for x in rows]) for k in ('env','tick','cost','phi_before','local_time','terminal','gamma')})
        summary.update(completed=True, strict_source_loaded=True, model_unchanged=unchanged,
            optimizer_updates_difference=0, episodes=reconciled, term_names=TERMS,
            input_sha256=pins, actual_initial_sha256={k:hashlib.sha256(v.tobytes()).hexdigest() for k,v in initial.items()},
            output_sha256={str(p):digest(p) for p in (out/'trace.npz',out/'initial.npz',out/'native/report.json',out/'native/episodes.jsonl')})
    except BaseException as error:
        summary['failure'] = type(error).__name__+': '+str(error)
        raise
    finally:
        (out/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
        (out/'SUMMARY.md').write_text('# 시점별 원본 보상 진단\n\n완료: '+str(summary['completed'])+'\n\n'
            '원본 strict 평균 정책 평가의 최초32 episode. 할인합과9항은 summary.json, 실제 q/hold는 initial.npz, 시점별 자료는 trace.npz. '
            '불완전 결과는 비교 대상이 아니다. Phi 이후값은 별도 geometry 호출로 측정하지 않았다.\n')


def run(checkpoint, out, variant):
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        return _run(checkpoint, out, variant)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--variant', choices=('base','no_prior'), required=True)
    args = parser.parse_args()
    runtime = STUDY/'runtime' if args.variant == 'base' else ROOT/'no_alignment_prior_variant/runtime'
    sys.path.insert(0, str(runtime))
    import isaacgym
    run(args.checkpoint.resolve(), args.out.resolve(), args.variant)
