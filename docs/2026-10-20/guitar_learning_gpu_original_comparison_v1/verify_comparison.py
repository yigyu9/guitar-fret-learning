"""Verify saved diagnostic evidence without importing native physics or changing sources."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REFERENCE = ROOT / 'docs/2026-10-20/guitar_learning_gpu_force_replay_v1/reference_n1/tape.npz'


def read(path):
    return json.loads(path.read_text())


def pair(first, second):
    result = {}
    with np.load(str(HERE / first / 'run/tape.npz')) as a, np.load(str(HERE / second / 'run/tape.npz')) as b:
        for key in ('body', 'q', 'qd'):
            x, y = a[key][:, 0], b[key][:, 0]
            assert x.shape == y.shape
            different = np.flatnonzero(np.any(x != y, axis=tuple(range(1, x.ndim))))
            result[key] = dict(snapshots=len(x), first_different_physics_step=int(different[0]) if len(different) else None,
                               max_abs_difference=float(np.abs(x - y).max()))
    return result


def main():
    pins = read(ROOT / 'docs/2026-10-20/guitar_learning_gpu_batch_v1/source_manifest.json')['active_python']
    changed = [p for p, expected in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != expected]
    assert not changed, changed
    cases = {}
    process_results = {row['case']: row for row in read(HERE / 'last_check_processes.json')}
    with np.load(str(REFERENCE)) as reference:
        for folder in sorted(HERE.iterdir()):
            if not folder.is_dir():
                continue
            case = {}
            variant_path = folder / 'variant.json'
            if variant_path.exists():
                variant = read(variant_path)
                assert variant['production_source_unchanged']
                assert hashlib.sha256((ROOT / 'guitar_learning/gpu/scene.py').read_bytes()).hexdigest() == variant['production_sha256']
                assert hashlib.sha256((folder / 'scene_variant.py.txt').read_bytes()).hexdigest() == variant['variant_sha256']
                case['saved_variant_sha_verified'] = True
            audit_path = folder / 'native_index_audit.json'
            if audit_path.exists():
                audit = read(audit_path)
                errors = sum(len(audit[k]) for k in ('actor_index_errors', 'dof_index_errors', 'body_index_errors'))
                assert errors == 0
                case['native_index_errors'] = errors
                case['native_counts'] = [audit[k] for k in ('sim_actor_count', 'sim_dof_count', 'sim_body_count')]
            report_path = folder / 'run/report.json'
            if report_path.exists():
                report = read(report_path)
                assert report['changed_inputs'] == []
                failure_steps = report['first_failure_physics_steps']
                case.update(completed=report['completed'], failure=report['failure'], steps=report['steps'],
                            num_envs=report['num_envs'], unsafe_envs=sum(v >= 0 for v in failure_steps),
                            first_unsafe_physics_step=min((v for v in failure_steps if v >= 0), default=None),
                            physics_gpu=report['scene']['physx_use_gpu'], tensor_gpu=report['scene']['use_gpu_pipeline'])
                with np.load(str(folder / 'run/tape.npz')) as tape:
                    for key in ('targets', 'efforts'):
                        assert np.array_equal(tape[key], reference[key][:len(tape[key])]), (folder.name, key)
                case['commands_equal_reference_prefix'] = True
            else:
                case['report_missing'] = True
                assert folder.name == 'subscene_one', folder
                case['native_process_returncode'] = process_results[folder.name]['returncode']
                assert case['native_process_returncode'] == -11
            shape_path = folder / 'shape_summary.json'
            if shape_path.exists():
                case['shapes'] = read(shape_path)
                assert case['shapes']['nonuniform_envs'] == 0
                assert case['shapes']['shape_rest_min'] == case['shapes']['shape_rest_max'] == 0
            force_path = folder / 'ground_contact_force.json'
            if force_path.exists():
                case['ground_contact_force'] = read(force_path)
                assert case['ground_contact_force']['max_abs_component_N'] > 0
            cases[folder.name] = case
    pairs = {name: pair(name + '_n1', name + '_n1024') for name in ('no_contact', 'noground', 'ground_only', 'ground_only_force')}
    for name in ('no_contact', 'ground_only', 'ground_only_force'):
        assert all(v['first_different_physics_step'] is None and v['snapshots'] == 129 for v in pairs[name].values())
    assert all(v['first_different_physics_step'] == 19 for v in pairs['noground'].values())
    parsed = []
    for path in sorted(HERE.glob('*.py')):
        ast.parse(path.read_text(), filename=str(path))
        parsed.append(path.name)
    result = dict(active_python_files_verified=len(pins), changed_active_python=changed,
                  cases=cases, env0_pairs=pairs, parsed_diagnostic_python=parsed,
                  scope='Identical-force open-loop diagnostic. Unsafe counts are distinct environments, not training episodes; contact-disabled runs are not stability tests.')
    (HERE / 'comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(active_python_files_verified=len(pins), cases=len(cases), env0_pairs=pairs), indent=2))


if __name__ == '__main__':
    main()
