"""Freeze new, authorized parallel inputs while retaining every sealed source."""
import json
from pathlib import Path

from prepare import STUDY, make_settings, load_cases, verify_pins, sha
from study_queue_v2 import verify_manifest
from guitar_learning.portability import portable, settings_digest


def save(path, value):
    path = Path(path).resolve(); path.relative_to(STUDY)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)


def freeze():
    path = STUDY/'설계/parallel_v1.json'
    if path.exists():
        raise FileExistsError('Parallel source/input manifest is immutable')
    parent_path = STUDY/'설계/queue_v2.json'
    parent = verify_manifest(parent_path)
    cases = load_cases(); first = cases[0]
    bundles = {j['case_id']: j['bundle'] for j in parent['jobs']}
    pilots = [(2, 20), (4, 20), (16, 10), (64, 10)]
    jobs = []
    for count, updates in pilots:
        identity = 'pilot_env'+str(count)
        jobs.append(dict(job_id=identity, case_id=first['case_id'], bundle=bundles[first['case_id']],
            mode='train', updates=updates, num_envs=count, horizon=32, size='medium', seed=7,
            pilot=True, out=str(STUDY/'로그/parallel_v1'/identity)))
    for case in cases:
        identity = case['case_id']
        train = dict(job_id=identity+'_train', case_id=identity, bundle=bundles[identity],
            mode='train', updates=100, num_envs=64, horizon=32, size='medium', seed=7, pilot=False,
            out=str(STUDY/'로그/parallel_v1/training'/identity))
        jobs.append(train)
        jobs.append(dict(job_id=identity+'_evaluate', case_id=identity, bundle=bundles[identity],
            mode='evaluate', train_job_id=train['job_id'], checkpoint=str(Path(train['out'])/'J/final.pt'),
            pilot=False, out=str(STUDY/'로그/parallel_v1/evaluation'/identity)))
    pins = dict(parent['pins']); pins[str(parent_path)] = sha(parent_path)
    for p in (STUDY/'도구').rglob('*.py'):
        if str(p) in pins and pins[str(p)] != sha(p):
            raise ValueError('Attempt to alter a sealed source: '+str(p))
        pins[str(p)] = sha(p)
    authorization = STUDY/'설계/parallel_authorization_v1.json'
    policy = json.loads(authorization.read_text())
    if policy.get('user_authorized') is not True:
        raise ValueError('Explicit authorization required')
    pins[str(authorization)] = sha(authorization)
    for job in jobs:
        if job['mode'] == 'train':
            case = next(c for c in cases if c['case_id'] == job['case_id'])
            settings = make_settings(case, job['bundle'], updates=job['updates'], num_envs=job['num_envs'],
                horizon=job['horizon'], size=job['size'], seed=job['seed'])
            settings_path = STUDY/'설계/parallel_settings_v1'/(job['job_id']+'.json')
            save(settings_path, portable(settings)); pins[str(settings_path)] = sha(settings_path)
            job['settings_sha256'] = settings_digest(settings)
    verify_pins(pins)
    save(path, dict(schema=parent['schema'], python=parent['python'], single_state=parent['single_state'],
        gpu_uuid=parent['gpu_uuid'], parallel_policy=policy, pins=pins, jobs=jobs,
        common_window_s=[3.3, 4.8], scientific_train_transitions=1228800,
        pilot_transitions=sum(n*u*32 for n, u in pilots), automatic_retry=False,
        parent_manifest_sha256=sha(parent_path)))
    verify_manifest(path)
    print(json.dumps(dict(manifest=str(path), jobs=len(jobs), pins=len(pins))))


if __name__ == '__main__':
    freeze()
