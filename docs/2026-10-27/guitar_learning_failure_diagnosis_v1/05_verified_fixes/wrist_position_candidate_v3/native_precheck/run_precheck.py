"""Original-CLI index/middle wrist-candidate-v3 precheck; dry by default, root executes."""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[2]
ROOT = DIAG.parents[2]
OLD = DIAG/'03_short_learning/other_finger_precheck_v3'
FINGERS = ('index', 'middle')
PREVIOUS = DIAG/'05_verified_fixes/wrist_position_jacobian_v2/other_finger_regression'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reused():
    return load(OLD/'run_prechecks.py', 'wrist_v2_other_original')


def reject_existing(path):
    if path.exists() or path.is_symlink():
        raise FileExistsError(str(path))


def jobs():
    old = reused()
    previous = load(PREVIOUS/'run_regression.py', 'candidate_v3_previous_jobs')
    result = []
    for sources, source_runs in ((old.jobs()[:4], OLD/'runs'), (previous.jobs()[:4], PREVIOUS/'runs')):
        for source in sources:
            job = copy.deepcopy(source)
            job['out'] = str(HERE/'runs'/job['name'])
            job['args'] = [value.replace(str(source_runs), str(HERE/'runs')) for value in job['args']]
            result.append(job)
    return result


def verify_seal(seal):
    baseline = reused().original()
    if any(not Path(p).is_file() or baseline.sha(p) != h for p, h in seal['input_pins'].items()):
        raise ValueError('Current candidate-v3 preparation changed')


def model_hash(model):
    import hashlib
    value = hashlib.sha256()
    for key, tensor in sorted(model.items()):
        value.update(key.encode())
        value.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return value.hexdigest()


def validate(job, seal):
    old = reused()
    baseline = old.original()
    checked = old.validate(job)
    out = Path(job['out'])
    settings = baseline.read(out/'settings.json')
    expected = baseline.read(HERE/'cpu_inputs'/(job['finger']+'_settings.json'))
    if settings != expected:
        raise ValueError('Exact current settings differ')
    report = baseline.read(out/'report.json')
    if report.get('changed_inputs') or report.get('unpinned_project_sources'):
        raise ValueError('Changed or unpinned child source')
    pins = baseline.read(out/'inputs_before.json')
    if any(p not in pins or pins[p] != h for p, h in seal['active_source_pins'].items()):
        raise ValueError('Current active source not fully pinned')
    scene = baseline.read(out/'gpu_scene_final.json')
    if (scene.get('physx_use_gpu') is not True or scene.get('use_gpu_pipeline') is not True
            or scene.get('environment_count') != 4 or scene.get('diagnostic_guitar_mode') != 'fixed'):
        raise ValueError('Require original fixed-guitar four-environment native scene')
    command = job['args'][job['args'].index(baseline.MODULE)+1:]
    if baseline.read(out/'invocation.json')['argv'][1:] != command:
        raise ValueError('Original CLI invocation differs')
    import torch
    if 'control' not in job:
        initial = torch.load(out/'initial.pt', map_location='cpu', weights_only=False)
        final = torch.load(out/'final.pt', map_location='cpu', weights_only=False)
        if (initial['updates'] != 0 or final['updates'] != 1 or len(initial['model']) != 73
                or initial['metadata']['settings'] != expected
                or model_hash(initial['model']) != seal['CPU_initial_model_sha256']
                or scene.get('physics_steps') != 128):
            raise ValueError('Own fresh initial or bootstrap budget differs')
        checked.update(actual_initial73_equal_CPU=True, initial_model_sha256=model_hash(initial['model']), initial_updates=0, final_updates=1)
    else:
        checkpoint = HERE/'runs'/(job['finger']+'_initial')/'initial.pt'
        evaluation = baseline.read(out/'evaluation.json')
        if (Path(command[command.index('--checkpoint')+1]) != checkpoint
                or pins.get(str(checkpoint)) != baseline.sha(checkpoint)
                or any(e['selected_target_count'] != 1 or e['target_id'] != expected['song']['short_learning']['teacher']['source_target_id']
                       for e in evaluation['episodes'])
                or not 0 < scene.get('physics_steps', -1) <= 4*expected['song']['short_learning']['view']['duration_ticks']
                or scene['physics_steps'] % 4):
            raise ValueError('Require own initial only, all four original first attempts and original native tick budget')
        meta = baseline.read(out/'trace_metadata.json')
        if (meta.get('wrist_candidate_arm_scope') != seal['wrist_control']['candidate_arm_scope']
                or meta.get('wrist_requested_delta_scope') != seal['wrist_control']['requested_delta_scope']):
            raise ValueError('Candidate/requested-delta trace scopes differ from current v3 contract')
        import numpy as np
        with np.load(out/'trace_env0_episode0.npz') as trace:
            samples = len(trace['time_s'])
            if (trace['wrist_candidate_arm_rad'].shape != (samples,12)
                    or not np.isfinite(trace['wrist_candidate_arm_rad']).all()):
                raise ValueError('Finite12-column env0 candidate trace required')
        checked.update(candidate_trace_samples=samples, candidate_trace_scope='env0 first attempt60Hz only')
    verify_seal(seal)
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='root GPU handoff only')
    args = parser.parse_args()
    plan, baseline = jobs(), reused().original()
    if not args.execute:
        print(json.dumps(dict(jobs=plan, GPU_executed=False, old_checkpoints_used=False), indent=2))
        return
    seal = baseline.read(HERE/'preparation_seal.json')
    if seal.get('independent_review') != 'passed_no_findings':
        raise ValueError('Independent CPU preparation review required; root executes after current source freeze and review')
    verify_seal(seal)
    base = HERE/'runs'
    reject_existing(base)
    base.mkdir(); (base/'logs').mkdir()
    env = os.environ.copy()
    env['PATH'] = str(baseline.PYTHON.parent)+os.pathsep+env.get('PATH', '')
    env.update(PYTHONPATH=str(ROOT/'isaacgym/python')+os.pathsep+str(ROOT),
               LD_LIBRARY_PATH=str(baseline.PYTHON.parent.parent/'lib'))
    identity = dict(script_sha256=baseline.sha(baseline.__file__), active_source_pins=seal['input_pins'])
    completed, started = [], time.monotonic()
    for job in plan:
        verify_seal(seal)
        reject_existing(Path(job['out']))
        baseline.run_child(job, base, env, identity)
        completed.append(dict(name=job['name'], launcher_returncode=0, validation=validate(job, seal)))
        print('COMPLETE '+job['name'], flush=True)
    baseline.write(base/'report.json', dict(completed=True, closed_scenes=8, stages=completed,
        wall_s=time.monotonic()-started, scope='own fresh initial only; four first attempts per condition including failures; not learned performance'))


if __name__ == '__main__':
    main()
