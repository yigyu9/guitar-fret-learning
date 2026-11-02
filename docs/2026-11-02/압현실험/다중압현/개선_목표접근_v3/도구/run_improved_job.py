"""Fresh E4 train/evaluation child; preserve the original strict runner contract.

Imports before the resource gate are standard-library only. The parent queue
must launch one child at a time with the verified GPU UUID visible.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

STUDY = Path(__file__).resolve().parents[1]
BASE = STUDY.parent/'학습_인접2지_v1'
ROOT = next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0, str(BASE/'도구'))
from study_queue_v2 import GPU_UUID, SINGLE, readiness as single_readiness
from study_queue_v2 import verify_manifest as verify_baseline

BASELINE_MANIFEST = BASE/'설계/after_parallel_hold_v1.json'
BASELINE_STATE = BASE/'로그/queue_after_parallel_v1/state.json'
CONDITION = dict(schema='multi_press.target_approach_condition.v3', condition='B2',
    natural_preparation=dict(schema='guitar_learning.natural_preparation.v3', condition='E4'),
    initialization='fresh', teacher=None)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(path):
    path = Path(path).resolve(); path.relative_to(STUDY)
    return path


def verify_manifest(path):
    data = json.loads(inside(path).read_text())
    if (data.get('schema') != 'multi_press.target_approach_training.v3' or
            data.get('sealed') is not True or data.get('condition') != CONDITION or
            data.get('gpu_uuid') != GPU_UUID or data.get('single_state') != str(SINGLE) or
            data.get('baseline_manifest') != str(BASELINE_MANIFEST) or
            data.get('baseline_state') != str(BASELINE_STATE) or
            data.get('common_window_s') != [3.3, 4.8] or
            data.get('evaluation_first_episode_denominator') != 32):
        raise ValueError('Sealed B2 E4/fresh/resource/evaluation identity required')
    pins = data.get('pins', {})
    required = [Path(__file__), STUDY/'도구/improved_environment.py',
                STUDY/'도구/prepare_improved_training.py', BASELINE_MANIFEST]
    if not pins or any(str(p.resolve()) not in pins for p in required):
        raise ValueError('B2 execution sources and parent manifest must be pinned')
    for filename, expected in pins.items():
        source = Path(filename).resolve(); source.relative_to(ROOT)
        if digest(source) != expected:
            raise ValueError('Pinned input changed: '+str(source))
    jobs = data['jobs']
    if (len(jobs) != 2 or [j['job_id'] for j in jobs] !=
            ['B2_index_middle_same_train', 'B2_index_middle_same_evaluate'] or
            [j['mode'] for j in jobs] != ['train', 'evaluate']):
        raise ValueError('Exactly the reviewed B2 train and first-episode evaluation required')
    for job in jobs:
        inside(job['out'])
        if (job['case_id'] != 'index_middle_same' or
                Path(job['bundle']).resolve() != BASE/'입력/song_bundles/index_middle_same'):
            raise ValueError('Only the reviewed readonly index/middle6/6 bundle is allowed')
    train, evaluate = jobs
    if (tuple(train.get(k) for k in ('updates', 'num_envs', 'horizon', 'seed', 'size')) !=
            (100, 64, 32, 7, 'medium') or
            str(inside(train['settings'])) not in pins or
            evaluate['train_job_id'] != train['job_id'] or
            Path(evaluate['checkpoint']).resolve() != inside(train['out'])/'J/final.pt'):
        raise ValueError('Fresh64/H32/100/seed7 settings and own checkpoint lineage required')
    parent = verify_baseline(BASELINE_MANIFEST)
    if any(pins.get(name) != expected for name, expected in parent['pins'].items()):
        raise ValueError('Every original source/input pin must be preserved')
    return data


def readiness():
    parent = verify_baseline(BASELINE_MANIFEST)
    state = json.loads(BASELINE_STATE.read_text())
    if (state.get('completed') is not True or state.get('status') != 'complete' or
            state.get('manifest_sha256') != digest(BASELINE_MANIFEST)):
        return False, 'waiting_for_original_six_case_queue', dict(baseline_status=state.get('status'))
    for job in parent['jobs']:
        row = state.get('jobs', {}).get(job['job_id'], {})
        expected = Path(job['out'])/'job_report.json'
        if (row.get('completed') is not True or row.get('report') != str(expected) or
                row.get('report_sha256') != digest(expected) or
                json.loads(expected.read_text()).get('completed') is not True):
            raise ValueError('Original baseline job/report identity is incomplete')
    return single_readiness()


@contextmanager
def runtime(manifest_path, manifest):
    from guitar_learning.training import rollout, finger_skill_runner
    from improved_environment import ImprovedPairEnvironment
    original_pool, original_pins = rollout.GpuPool, finger_skill_runner._pins
    class ImprovedPool(original_pool):
        environment_class_override = ImprovedPairEnvironment
    def pins(settings, out, extra=()):
        return original_pins(settings, out, list(extra)+
            [Path(p) for p in manifest['pins']]+[Path(manifest_path)])
    rollout.GpuPool, finger_skill_runner._pins = ImprovedPool, pins
    try:
        yield finger_skill_runner
    finally:
        rollout.GpuPool, finger_skill_runner._pins = original_pool, original_pins


def verify_eval_identity(payload, job, train, report, checkpoint_sha):
    from guitar_learning.portability import localize, settings_digest
    settings = localize(payload['metadata']['settings'])
    experiment = settings.get('experiment', {})
    natural = payload['identity']['architecture']['contract']['reward'].get('natural_preparation', {})
    expected = inside(train['out'])/'J/final.pt'
    if (settings_digest(settings) != train['settings_sha256'] or
            experiment.get('improvement') != CONDITION or
            natural.get('schema') != 'guitar_learning.natural_preparation.v3' or
            natural.get('condition') != 'E4' or
            Path(job['checkpoint']).resolve() != expected or
            report.get('job_id') != train['job_id'] or report.get('condition') != CONDITION or
            report.get('case_id') != 'index_middle_same' or report.get('completed') is not True or
            report.get('checkpoint') != str(expected) or report.get('checkpoint_sha256') != checkpoint_sha):
        raise ValueError('E4 checkpoint settings/architecture/verified training parent mismatch')


def run(manifest_path, identity):
    path = inside(manifest_path); manifest = verify_manifest(path)
    matches = [j for j in manifest['jobs'] if j['job_id'] == identity]
    if len(matches) != 1:
        raise ValueError('Unknown B2 job')
    job = matches[0]; out = inside(job['out'])
    if out.exists():
        raise FileExistsError('Fresh B2 output required; no implicit resume/retry')
    ready, reason, resource = readiness()
    if not ready or os.environ.get('CUDA_VISIBLE_DEVICES') != GPU_UUID:
        raise RuntimeError('B2 refused before Gym import: '+reason)
    import isaacgym  # Must precede Torch/NumPy/policy imports.
    from prepare_improved_training import improved_settings
    from run_job_v2 import joint_summary
    from guitar_learning.portability import settings_digest
    error = None; result = None; summary = None; checkpoint = None; checkpoint_sha = None
    try:
        with runtime(path, manifest) as runner:
            if job['mode'] == 'train':
                settings = improved_settings()
                if settings_digest(settings) != job['settings_sha256']:
                    raise ValueError('Regenerated E4 settings differ from reviewed frozen settings')
                result = runner.run(settings, SimpleNamespace(out=out, resume=None))
                phase = json.loads((out/'J/report.json').read_text())
                if (result.get('completed') is not True or phase.get('completed') is not True or
                        phase.get('updates_in_run') != 100 or phase.get('transitions') != 204800):
                    raise RuntimeError('E4 training budget/lifecycle failed')
                checkpoint = out/'J/final.pt'; checkpoint_sha = digest(checkpoint)
                episodes = [json.loads(l)['episode'] for l in (out/'J/episodes.jsonl').read_text().splitlines()]
            else:
                import torch
                checkpoint = inside(job['checkpoint']); checkpoint_sha = digest(checkpoint)
                payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
                runner._validate_metadata_schema(payload['metadata'])
                runner._validate_pins(payload['metadata'])
                train = manifest['jobs'][0]
                report = json.loads((inside(train['out'])/'job_report.json').read_text())
                verify_eval_identity(payload, job, train, report, checkpoint_sha)
                result, episodes = runner.evaluate_checkpoint(checkpoint, out, num_envs=32,
                    scope='full_song', max_batches=1, max_episodes=32)
                if result.get('completed') is not True or len(episodes) != 32:
                    raise RuntimeError('Exactly32 first-episode evaluation/lifecycle required')
            summary = joint_summary(episodes)
        verify_manifest(path)
    except BaseException as exc:
        error = type(exc).__name__+': '+str(exc)
        raise
    finally:
        out.mkdir(parents=True, exist_ok=True)
        record = dict(schema='multi_press.target_approach_job.v3', job_id=identity,
            case_id='index_middle_same', condition=CONDITION, mode=job['mode'],
            completed=error is None and result is not None, error=error,
            source_manifest=str(path), source_manifest_sha256=digest(path),
            resource_before=resource, simultaneous_summary=summary,
            checkpoint=str(checkpoint) if checkpoint else None, checkpoint_sha256=checkpoint_sha,
            scope='Explicit E4 preparation reward/observation condition; unchanged J33 PPO/control/physics; no acoustic certification')
        with (out/'job_report.json').open('x', encoding='utf-8') as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2, allow_nan=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--job', required=True)
    args = parser.parse_args()
    run(args.manifest, args.job)
