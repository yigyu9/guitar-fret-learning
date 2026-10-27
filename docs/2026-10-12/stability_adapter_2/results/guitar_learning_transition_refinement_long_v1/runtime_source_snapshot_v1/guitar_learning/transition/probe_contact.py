"""Native feedback-teacher capture using the unchanged audited probe writer."""
import argparse
import os
from pathlib import Path


def run(settings, args):
    from unittest.mock import patch
    from . import environment, probe, solver, teacher
    from .contact_teacher import Controller, input_paths

    if settings['transition']['role'] != 'left':
        raise ValueError('feedback capture currently supports the left role only')
    if getattr(args, 'checkpoint', None) is not None:
        raise ValueError('feedback teacher is not an unassisted policy evaluation')
    original_build, original_paths = environment.build_environment, solver.input_paths
    contact_paths = input_paths()
    current = {}

    def build(*values, **kwargs):
        env = original_build(*values, **kwargs)
        current['environment'] = env
        return env

    def paths(asset_path=None):
        return sorted(set(original_paths(asset_path)) | set(contact_paths))

    class BoundController:
        def __init__(self, plan, task, transition=None):
            if 'environment' not in current:
                raise RuntimeError('native environment must precede feedback controller')
            self.controller = Controller(plan, task, transition)
            self.env = current['environment']

        @property
        def diagnostic(self):
            return self.controller.diagnostic

        def action(self, now):
            return self.controller.action(now, env=self.env)

    args.controller = 'solver'
    with patch.object(environment, 'build_environment', build), \
            patch.object(solver, 'input_paths', paths), \
            patch.object(teacher, 'Controller', BoundController):
        return probe.run(settings, args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--episodes', type=int, default=1)
    parser.add_argument('--max-nfev', type=int, default=80)
    parser.add_argument('--starts', type=int, default=2)
    args = parser.parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    import isaacgym
    import json
    from .train import settings_document
    run(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__':
    main()
