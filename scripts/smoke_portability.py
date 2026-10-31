#!/usr/bin/env python3
"""Short real portability checks; never substitutes CPU/mock work for GPU results."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[1]


def copy_runtime_project(destination):
    """Copy active inputs, not historical experiment trees or external symlinks."""
    destination.mkdir(parents=True, exist_ok=False)
    bytecode = shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
    def ignore(directory, names):
        excluded = set(bytecode(directory, names))
        # assets/runtime_inputs/.../archive holds required immutable inputs.
        if Path(directory) == PROJECT / 'guitar_learning':
            excluded.add('archive')
        return excluded
    for name in ('guitar_learning', 'scripts'):
        shutil.copytree(str(PROJECT / name), str(destination / name), ignore=ignore, symlinks=True)
    shutil.copytree(str(PROJECT / 'isaacgym/python/isaacgym'),
                    str(destination / 'isaacgym/python/isaacgym'), ignore=ignore, symlinks=True)
    shutil.copy2(str(PROJECT / 'isaacgym/python/setup.py'),
                 str(destination / 'isaacgym/python/setup.py'))
    shutil.copytree(str(PROJECT / 'data/song_bundles/05_BN2-131-B_solo'),
                    str(destination / 'data/song_bundles/05_BN2-131-B_solo'), symlinks=True)
    for name in ('README.md', 'PROJECT_CONTEXT.md', 'CURRENT_STATUS.md'):
        shutil.copy2(str(PROJECT / name), str(destination / name))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cache-root', type=Path, required=True)
    parser.add_argument('--relocate-to', type=Path)
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    project = PROJECT
    if args.relocate_to:
        project = args.relocate_to.resolve()
        copy_runtime_project(project)
    try:
        out.relative_to(project)
    except ValueError:
        parser.error('--out must be inside the target project for project-local input verification')
    out.mkdir(parents=True, exist_ok=False)
    launcher = [sys.executable, str(project / 'scripts/tab2body.py'),
                '--cache-root', str(args.cache_root.resolve())]
    report = dict(schema='tab2body.portability_smoke.v1', project=str(project),
                  original_project=str(PROJECT), python=sys.executable, stages=[])

    def stage(name, command, requires=None):
        if requires and not requires['passed']:
            result = dict(name=name, passed=False, skipped=True,
                          reason='prerequisite failed: ' + requires['name'])
        else:
            started = time.monotonic()
            logfile = out / (name + '.log')
            with logfile.open('x') as stream:
                try:
                    run = subprocess.run(command, cwd=str(out), stdout=stream,
                                         stderr=subprocess.STDOUT, timeout=600)
                    result = dict(name=name, passed=run.returncode == 0,
                                  returncode=run.returncode, command=command)
                except subprocess.TimeoutExpired:
                    result = dict(name=name, passed=False, reason='600s timeout', command=command)
            result.update(log=logfile.name, wall_s=time.monotonic() - started)
        report['stages'].append(result)
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        return result

    prepared = stage('local_runtime', launcher + ['prepare'])
    inputs = stage('inputs', launcher + ['run', '-m',
        'guitar_learning.tool.validation.portable_inputs', '--out', str(out / 'inputs.json')], prepared)
    probe = stage('gpu_probe', launcher + ['probe'], prepared)
    train_args = ['--size', 'small', '--num-envs', '2', '--horizon', '2', '--updates', '1']
    train = stage('train', launcher + ['run', '-m', 'guitar_learning.train'] + train_args +
                  ['--out', str(out / 'train')], probe if not probe['passed'] else inputs)
    checkpoint = out / 'train/J/final.pt'
    resume = stage('resume', launcher + ['run', '-m', 'guitar_learning.train'] + train_args +
                   ['--resume', str(checkpoint), '--out', str(out / 'resume')], train)
    stage('evaluation', launcher + ['run', '-m',
          'guitar_learning.tool.evaluation.evaluate_finger_skill', str(checkpoint),
          '--num-envs', '2', '--scope', 'full_song', '--out', str(out / 'evaluation')], train)
    if args.render:
        stage('render', launcher + ['run', '-m',
              'guitar_learning.tool.demonstration.render_finger_skill',
              '--checkpoint', str(checkpoint), '--num-envs', '2',
              '--scope', 'full_song', '--out', str(out / 'render')], train)
    report['completed'] = all(item['passed'] for item in report['stages'])
    report['research_success_claimed'] = False
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return 0 if report['completed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
