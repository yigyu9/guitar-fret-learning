"""원래 단계 이전 API로 가중치만 옮겨 0업데이트 모델을 내보낸다.

학습·압현 평가·승급을 수행하지 않는다. 내보낸 모델은 봉인된 기본 평가/영상 도구로
읽으며, 이 스크립트는 생성 출처로만 기록되고 이후 실행의 필수 코드가 아니다.
"""
if __name__ == '__main__':
    import isaacgym  # native 라이브러리는 torch보다 먼저 불러온다.

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parents[1]
RUNTIME = STUDY/'runtime'
sys.path.insert(0, str(RUNTIME))
STAGES = ('B', 'C50', 'C75', 'C100', 'free_v9')
DISTRIBUTIONS = ('saved', 'aligned', 'v9')


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def verify_seal():
    path = STUDY/'source_seal.json'
    seal = json.loads(path.read_text())
    if len(seal['files']) != 3148:
        raise ValueError('expected immutable 3148-file source seal')
    changed = [name for name, sha in seal['files'].items()
               if not (RUNTIME/name).is_file() or digest(RUNTIME/name) != sha]
    if changed:
        raise ValueError('frozen runtime changed: '+str(changed[:8]))
    return digest(path)


def make_settings(saved_settings, source, stage, distribution, sp):
    if stage not in STAGES or distribution not in DISTRIBUTIONS:
        raise ValueError('explicit supported stage and initial distribution required')
    if distribution != 'saved' and stage != 'free_v9':
        raise ValueError('initial-distribution overrides are only permitted for free_v9')
    if saved_settings['size'] != 'large':
        raise ValueError('this model-only export requires a large source model')
    old = saved_settings['structured_press']
    settings = sp.build_settings(old['song'], stage, old['geometry'], num_envs=64,
        updates=100, size='large', seed=saved_settings['seed'])
    config = settings['structured_press']
    if distribution != 'saved':
        config['initial_distribution']['v9_fraction'] = 0. if distribution == 'aligned' else 1.
    settings['structured_transfer'] = dict(source=str(Path(source).resolve()), sha256=digest(source),
        scope='model weights only; fresh Adam/RNG; zero-update stage initialization')
    fraction = config['initial_distribution']['v9_fraction']
    start = 'aligned' if fraction == 0 else 'v9' if fraction == 1 else 'mixed_v9_'+str(fraction)
    support = 'no_support_J33' if stage == 'free_v9' else 'saved_stage_support'
    settings['simple_start']['initial_pose'] = 'structured_press_v2:'+stage+':'+start+':'+support
    return settings


@contextmanager
def creation_provenance(official, source, transition):
    """외부 생성 입력은 required runtime이 아니라 검증한 생성 계보로 봉인한다."""
    original_pins, original_metadata = official._pins, official.checkpoint_metadata
    creation = [Path(source).resolve(), Path(__file__).resolve()]
    def pins(settings, out, extra=()):
        return original_pins(settings, out, list(extra)+creation)
    def metadata(*args, **kwargs):
        lineage = [Path(value).resolve() for value in kwargs.get('lineage', ())]
        kwargs['lineage'] = list(dict.fromkeys(lineage+creation))
        kwargs.update(model_only_transition=transition, optimizer_updates=0,
            committed_transitions=0, no_training=True, not_formal_stage_pass=True)
        return original_metadata(*args, **kwargs)
    official._pins, official.checkpoint_metadata = pins, metadata
    try:
        yield
    finally:
        official._pins, official.checkpoint_metadata = original_pins, original_metadata


def verify_export(source_payload, target, config, torch):
    exported = torch.load(target, map_location='cpu', weights_only=False)
    expected, actual = source_payload['model'], exported['model']
    if set(expected) != set(actual):
        raise ValueError('source/export model tensor keys differ')
    different = [name for name in expected if name != 'active_mask' and
                 not torch.equal(expected[name], actual[name])]
    if different:
        raise ValueError('model weights changed during zero-update transfer: '+str(different[:8]))
    if actual['active_mask'].nonzero().flatten().tolist() != config['active_axes']:
        raise ValueError('export active mask does not match target stage')
    if exported['updates'] != 0 or exported['actor_optimizer']['state'] or exported['value_optimizer']['state']:
        raise ValueError('export must have zero updates and empty fresh optimizer states')
    metadata = exported['metadata']
    if metadata['curriculum']['committed_transitions'] != 0 or not metadata.get('no_training'):
        raise ValueError('export metadata must identify zero committed transitions and no training')
    return dict(path=str(target), sha256=digest(target), exact_source_model_except_active_mask=True,
                optimizer_updates=0, fresh_optimizer_states_empty=True)


def run(source, stage, distribution, out):
    source, out = Path(source).resolve(), Path(out).resolve()
    if out.exists():
        raise FileExistsError('existing export output must not be overwritten: '+str(out))
    source_sha, script_sha, seal_sha = digest(source), digest(__file__), verify_seal()
    started = time.monotonic()
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        import torch
        from guitar_learning.portability import localize
        from guitar_learning.training import finger_skill_runner as official
        from guitar_learning.tool.experiments import structured_press as sp
        source_payload = torch.load(source, map_location='cpu', weights_only=False)
        official._validate_metadata_schema(source_payload.get('metadata'))
        official._validate_pins(source_payload['metadata'])
        saved = localize(source_payload['metadata']['settings'])
        settings = make_settings(saved, source, stage, distribution, sp)
        config = settings['structured_press']
        transition = dict(source=str(source), source_sha256=source_sha,
            source_optimizer_updates=source_payload['updates'], target_stage=stage,
            requested_initial_distribution=distribution, saved_initial_distribution=config['initial_distribution'],
            source_optimizer_or_rng_transferred=False, model_weights_only=True,
            optimizer_updates=0, committed_transitions=0, no_training=True, not_formal_stage_pass=True)
        spec = settings['finger_skill']
        schedule = official.ExposureSchedule(spec['planned_transitions'], spec['full_song_after'])
        out.mkdir(parents=True, exist_ok=False)
        outer = dict(schema='structured_press.model_only_transition.v1', completed=False,
            model_only_transition=transition, no_training=True, not_formal_stage_pass=True,
            optimizer_updates=0, committed_transitions=0, physics_steps=None,
            started_utc=datetime.now(timezone.utc).isoformat(), source_sha256=source_sha,
            creation_script_sha256=script_sha, frozen_source_seal_sha256=seal_sha)
        try:
            # initialize_from가 원래 source architecture/input/schema 검증과 인접 단계 제한을 수행한다.
            with sp.structured_runtime(config, initialize_from=source):
                with creation_provenance(official, source, transition):
                    result = official._train_phase(settings, out/'J', schedule, updates=0)
            report = result['report']
            outer.update(physics_steps=report['gpu_scene']['physics_steps'],
                optimizer_updates=report['optimizer_updates'], committed_transitions=schedule.committed_transitions)
            if (not report['completed'] or report['optimizer_updates'] != 0 or report['updates_in_run'] != 0 or
                    report['transitions'] != 0 or report['gpu_scene']['physics_steps'] != 0 or
                    schedule.committed_transitions != 0):
                raise ValueError('zero-update export unexpectedly trained, simulated, or did not finish validation')
            exports = [verify_export(source_payload, out/'J'/name, config, torch)
                       for name in ('initial.pt', 'final.pt')]
            if digest(source) != source_sha or digest(__file__) != script_sha or verify_seal() != seal_sha:
                raise ValueError('source model, creation tool or frozen runtime changed during export')
            outer.update(completed=True, exports=exports, checkpoint=str(out/'J/final.pt'),
                original_source_unchanged=True, creation_script_unchanged=True,
                base_run_report=str(out/'J/report.json'), lifecycle_verified=report['lifecycle_verified'],
                limitation='model initialization only; no performance evaluation or formal stage promotion')
        except BaseException as error:
            outer.update(failure=dict(type=type(error).__name__, message=str(error)))
            raise
        finally:
            outer['wall_s'] = time.monotonic()-started
            (out/'report.json').write_text(json.dumps(outer, ensure_ascii=False, indent=2)+'\n')
    return outer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--stage', required=True, choices=STAGES)
    parser.add_argument('--initial-distribution', default='saved', choices=DISTRIBUTIONS)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    run(args.checkpoint, args.stage, args.initial_distribution, args.out)


if __name__ == '__main__':
    main()
