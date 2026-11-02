"""Use the unmodified J33 trainer with a diagnostic-only environment subclass."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
from types import SimpleNamespace

from study_queue import STUDY, GPU_UUID, atomic, inside, digest, readiness, verify_manifest


@contextmanager
def runtime(manifest_path, manifest):
    # Official environment hook; preserve native runner/checkpoint validation.
    from guitar_learning.training import rollout, finger_skill_runner
    from pair_environment import PairEnvironment
    original_pool, original_pins = rollout.GpuPool, finger_skill_runner._pins
    class PairPool(original_pool):
        environment_class_override = PairEnvironment
    extra_sources = [Path(name) for name in manifest['pins']]+[Path(manifest_path)]
    def pins(settings, out, extra=()):
        return original_pins(settings, out, list(extra)+extra_sources)
    rollout.GpuPool, finger_skill_runner._pins = PairPool, pins
    try:
        yield finger_skill_runner
    finally:
        rollout.GpuPool, finger_skill_runner._pins = original_pool, original_pins


def joint_summary(episodes):
    if not episodes:
        return dict(denominator=0, successes=0, mean_fraction=None, longest_clean_s=None)
    values = [e['simultaneous_press'] for e in episodes]
    return dict(denominator=len(values), successes=sum(bool(v['success']) for v in values),
                mean_fraction=sum(v['clean_fraction'] for v in values)/len(values),
                longest_clean_s=max(v['longest_clean_s'] for v in values),
                individual_two_achieved=sum(all(v['individual_achievements']) for v in values),
                wrong_union_s=sum(v['wrong_union_s'] for v in values))


def verify_eval_identity(metadata, job, target_ids, train_job, train_report, checkpoint_sha):
    from guitar_learning.portability import localize
    settings = localize(metadata['settings'])
    experiment = settings.get('experiment', {})
    if (experiment.get('schema') != 'multi_press.adjacent_pair_training.v1' or
            experiment.get('case_id') != job['case_id'] or experiment.get('target_ids') != target_ids or
            experiment.get('common_window_s') != [3.3, 4.8] or
            Path(settings['song_training']['bundle']).resolve() != Path(job['bundle']).resolve()):
        raise ValueError('Evaluation checkpoint case/targets/bundle mismatch')
    expected = inside(train_job['out'])/'J/final.pt'
    if (train_job['mode'] != 'train' or train_job['case_id'] != job['case_id'] or
            train_job['job_id'] != job['train_job_id'] or
            Path(job['checkpoint']).resolve() != expected or
            train_report.get('job_id') != train_job['job_id'] or
            train_report.get('case_id') != job['case_id'] or train_report.get('completed') is not True or
            train_report.get('checkpoint') != str(expected) or
            train_report.get('checkpoint_sha256') != checkpoint_sha):
        raise ValueError('Evaluation checkpoint differs from verified preceding training')


def run(manifest_path, identity):
    manifest_path = inside(manifest_path)
    manifest = verify_manifest(manifest_path)
    matches = [j for j in manifest['jobs'] if j['job_id'] == identity]
    if len(matches) != 1:
        raise ValueError('Unknown job identity')
    job = matches[0]; out = inside(job['out'])
    if out.exists():
        raise FileExistsError('Fresh native job output required')
    ready, reason, resource = readiness()
    if not ready or os.environ.get('CUDA_VISIBLE_DEVICES') != GPU_UUID:
        raise RuntimeError('Native job refused before Gym import: '+reason)
    # Native extension must be imported before Torch/NumPy and policy code.
    import isaacgym
    from prepare import load_cases, make_settings, task_for_case
    case = next(c for c in load_cases() if c['case_id'] == job['case_id'])
    task = task_for_case(case, job['bundle'])
    error = None; result = None; summary = None; checkpoint_path = None; checkpoint_sha = None
    try:
        with runtime(manifest_path, manifest) as runner:
            if job['mode'] == 'train':
                settings = make_settings(case, job['bundle'], updates=job['updates'],
                    num_envs=job['num_envs'], horizon=job['horizon'], size=job['size'], seed=job['seed'])
                from guitar_learning.portability import settings_digest
                if settings_digest(settings) != job['settings_sha256']:
                    raise ValueError('Regenerated settings differ from frozen reviewed settings')
                result = runner.run(settings, SimpleNamespace(out=out, resume=None))
                phase = json.loads((out/'J/report.json').read_text())
                if (result.get('completed') is not True or phase.get('completed') is not True or
                        phase.get('updates_in_run') != job['updates']):
                    raise RuntimeError('Training report/budget/lifecycle not verified')
                checkpoint_path = out/'J/final.pt'; checkpoint_sha = digest(checkpoint_path)
                path = out/'J/episodes.jsonl'
                episodes = [json.loads(line)['episode'] for line in path.read_text().splitlines()]
                summary = joint_summary(episodes)
            else:
                checkpoint = inside(job['checkpoint'])
                import torch
                payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
                runner._validate_metadata_schema(payload['metadata'])
                runner._validate_pins(payload['metadata'])
                train_job = next(j for j in manifest['jobs'] if j['job_id'] == job['train_job_id'])
                train_report = json.loads((inside(train_job['out'])/'job_report.json').read_text())
                checkpoint_path, checkpoint_sha = checkpoint, digest(checkpoint)
                verify_eval_identity(payload['metadata'], job, [t.target_id for t in task.targets],
                                     train_job, train_report, checkpoint_sha)
                result, episodes = runner.evaluate_checkpoint(checkpoint, out, num_envs=32,
                    scope='full_song', max_batches=1, max_episodes=32)
                if result.get('completed') is not True or len(episodes) != 32:
                    raise RuntimeError('First-episode evaluation denominator/lifecycle not verified')
                summary = joint_summary(episodes)
        verify_manifest(manifest_path)
    except BaseException as exc:
        error = type(exc).__name__+': '+str(exc)
        raise
    finally:
        out.mkdir(parents=True, exist_ok=True)
        atomic(out/'job_report.json', dict(schema='multi_press.native_job.v1', job_id=identity,
            case_id=case['case_id'], mode=job['mode'], completed=error is None and result is not None,
            error=error, source_manifest=str(manifest_path), source_manifest_sha256=digest(manifest_path),
            resource_before=resource, common_window_s=[3.3, 4.8], simultaneous_summary=summary,
            checkpoint=str(checkpoint_path) if checkpoint_path else None, checkpoint_sha256=checkpoint_sha,
            scope='Unchanged J33 PPO/physics; simultaneous diagnostics added. No acoustic certification.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--job', required=True)
    args = parser.parse_args()
    run(args.manifest, args.job)
