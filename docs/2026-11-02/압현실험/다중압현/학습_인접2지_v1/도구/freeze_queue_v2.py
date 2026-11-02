"""Freeze reviewable settings and all immutable inputs before queue dispatch."""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path

from prepare import STUDY, ROOT, load_cases, make_settings, verify_pins, sha
from study_queue_v2 import SINGLE, GPU_UUID, verify_manifest
from guitar_learning.portability import portable, settings_digest


def save_new(path, document):
    path = Path(path).resolve(); path.relative_to(STUDY)
    payload = json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)


def freeze(python):
    manifest_path = STUDY/'설계/queue_v2.json'
    if manifest_path.exists():
        raise FileExistsError('Queue manifest is immutable; use a new study version')
    python = Path(python).resolve()
    if not python.is_file():
        raise ValueError('Installed native Python interpreter required')
    input_report_path = STUDY/'입력/song_bundles/report.json'
    prepared = json.loads(input_report_path.read_text())
    if prepared.get('completed') is not True or len(prepared['rows']) != 6:
        raise ValueError('Six complete input bundles required')
    verify_pins(prepared['source_sha256']); verify_pins(prepared['output_sha256'])
    pins = dict(prepared['source_sha256']); pins.update(prepared['output_sha256'])
    old_protected = STUDY.parent/'입력/protected_sha256.json'
    protected = json.loads(old_protected.read_text()); verify_pins(protected)
    for name, value in protected.items():
        if name in pins and pins[name] != value:
            raise ValueError('Conflicting earlier source expectation: '+name)
        pins.setdefault(name, value)
    static_paths = [input_report_path, old_protected, ROOT/'scripts/tab2body.py',
                    STUDY/'설계/queue_v2_origin.json']
    static_paths.extend((STUDY/'도구').rglob('*.py'))
    by_case = {r['case_id']: r['bundle'] for r in prepared['rows']}
    jobs = []
    cases = load_cases()
    for index, case in enumerate(cases):
        if index == 0:
            jobs.append(dict(job_id='smoke', mode='train', case_id=case['case_id'],
                bundle=by_case[case['case_id']], updates=1, num_envs=2, horizon=2,
                size='medium', seed=7, out=str(STUDY/'로그/smoke_v2')))
        identity = case['case_id']
        train = dict(job_id=identity+'_train', mode='train', case_id=identity, bundle=by_case[identity],
            updates=100, num_envs=64, horizon=32, size='medium', seed=7,
            out=str(STUDY/'로그/training_v2'/identity))
        jobs.append(train)
        jobs.append(dict(job_id=identity+'_evaluate', mode='evaluate', case_id=identity,
            bundle=by_case[identity], checkpoint=str(Path(train['out'])/'J/final.pt'),
            train_job_id=train['job_id'], out=str(STUDY/'로그/evaluation_v2'/identity)))
    for job in jobs:
        if job['mode'] == 'train':
            case = next(c for c in cases if c['case_id'] == job['case_id'])
            settings = make_settings(case, job['bundle'], updates=job['updates'],
                num_envs=job['num_envs'], horizon=job['horizon'], size=job['size'], seed=job['seed'])
            path = STUDY/'설계/settings_queue_v2'/(job['job_id']+'.json')
            save_new(path, portable(settings)); static_paths.append(path)
            job['settings_sha256'] = settings_digest(settings)
    for path in static_paths:
        pins[str(path.resolve())] = sha(path)
    verify_pins(pins)
    save_new(manifest_path, dict(schema='multi_press.training_queue.v1', python=str(python),
        created_kst=datetime.now(timezone(timedelta(hours=9))).isoformat(),
        single_state=str(SINGLE), gpu_uuid=GPU_UUID,
        common_window_s=[3.3, 4.8], pins=pins, jobs=jobs,
        scientific_train_transitions=1228800, smoke_transitions=4,
        evaluation_first_episode_denominator_each=32,
        reward_physics_control_changes=False, automatic_retry=False))
    verify_manifest(manifest_path)
    print(json.dumps(dict(manifest=str(manifest_path), jobs=len(jobs), pinned_files=len(pins))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--python', required=True)
    args = parser.parse_args()
    freeze(args.python)
