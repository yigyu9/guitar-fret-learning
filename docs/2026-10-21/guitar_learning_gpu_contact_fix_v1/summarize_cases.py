"""Check preserved command tapes and summarize contact diagnostic cases."""
import ast
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def main():
    pins = json.loads((HERE / 'inputs_before.json').read_text())
    changed = [p for p, digest in pins.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != digest]
    cases = {}
    for folder in sorted(HERE.iterdir()):
        report_path = folder / 'run/report.json'
        if not report_path.exists():
            continue
        report = json.loads(report_path.read_text())
        reference = np.load(report['replay'])
        steps = report['first_failure_physics_steps']
        value = dict(completed=report['completed'], failure=report['failure'], steps=report['steps'],
                     num_envs=report['num_envs'], unsafe_envs=sum(v >= 0 for v in steps),
                     first_unsafe_physics_step=min((v for v in steps if v >= 0), default=None),
                     max_speed_rad_s=max((v['max_speed_rad_s'] for v in report['rows']), default=None))
        tape = np.load(str(folder / 'run/tape.npz'))
        for key in ('efforts', 'targets'):
            assert np.array_equal(tape[key], reference[key][:len(tape[key])]), (folder, key)
        assert report['changed_inputs'] == []
        variant_path = folder / 'variant.json'
        if variant_path.exists():
            variant = json.loads(variant_path.read_text())
            if 'production_unchanged' in variant:
                assert variant['production_unchanged']
                assert hashlib.sha256((folder / 'scene_source.py.txt').read_bytes()).hexdigest() == variant['runtime_source_sha256']
            else:
                assert variant['production_source_unchanged']
                assert hashlib.sha256((folder / 'scene_variant.py.txt').read_bytes()).hexdigest() == variant['variant_sha256']
        value['same_commands'] = True
        first_path = HERE / folder.name.replace('_n1024', '_n1') / 'run/tape.npz'
        if folder.name.endswith('_n1024') and first_path.exists():
            first = np.load(str(first_path))
            pairs = {}
            for key in ('body', 'q', 'qd'):
                n = min(len(first[key]), len(tape[key]))
                a, b = first[key][:n, 0], tape[key][:n, 0]
                bad = np.flatnonzero(np.any(a != b, axis=tuple(range(1, a.ndim))))
                pairs[key] = dict(snapshots=n, first_different_physics_step=int(bad[0]) if len(bad) else None)
            value['env0_pair'] = pairs
        cases[folder.name] = value
    for path in HERE.glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    result = dict(changed_production_inputs=changed, cases=cases,
                  scope='Open-loop native diagnostic; unsafe counts are distinct environments, not training episodes. No-contact variants are not fixes.')
    (HERE / 'case_summary.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(cases=len(cases), changed_production_inputs=changed)))


if __name__ == '__main__':
    main()
