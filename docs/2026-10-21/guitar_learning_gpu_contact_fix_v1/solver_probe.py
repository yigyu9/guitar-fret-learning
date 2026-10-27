"""One-variable native integration accuracy diagnostics over the compound probe."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

p = argparse.ArgumentParser(add_help=False)
p.add_argument('--position-iterations', type=int)
p.add_argument('--substeps', type=int)
options, remaining = p.parse_known_args()
if (options.position_iterations is None) == (options.substeps is None):
    p.error('Exactly one diagnostic solver parameter required')
import isaacgym
from isaacgym import gymapi

out = Path(remaining[remaining.index('--out') + 1])
acquire = gymapi.acquire_gym


class ParamsProxy:
    def __init__(self, gym):
        self.gym = gym

    def __getattr__(self, name):
        return getattr(self.gym, name)

    def create_sim(self, compute, graphics, engine, params):
        before = dict(position_iterations=params.physx.num_position_iterations, substeps=params.substeps)
        if options.position_iterations is not None:
            params.physx.num_position_iterations = options.position_iterations
        else:
            params.substeps = options.substeps
        sim = self.gym.create_sim(compute, graphics, engine, params)
        if sim is None:
            raise RuntimeError('Native diagnostic simulator creation failed')
        actual = self.gym.get_sim_params(sim)
        after = dict(position_iterations=actual.physx.num_position_iterations, substeps=actual.substeps)
        if options.position_iterations is not None:
            assert after['position_iterations'] == options.position_iterations
        else:
            assert after['substeps'] == options.substeps
        with (out / 'solver_change.json').open('x') as stream:
            json.dump(dict(before=before, actual=after,
                           driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), stream, indent=2)
        return sim


gymapi.acquire_gym = lambda: ParamsProxy(acquire())
helper = Path(__file__).with_name('compound_probe.py')
sys.argv = [str(helper)] + remaining
runpy.run_path(str(helper), run_name='__main__')
