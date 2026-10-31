"""PPO from reset: former settling2s is now goal-observed policy preparation."""
import argparse
import copy
import json
import os
from pathlib import Path
import random
from unittest.mock import patch

from guitar_learning.tool.training import train_timing


def settings_document(raw):
    settings = train_timing.settings_document(raw)
    if settings['timing']['pre_roll_s'] != 3.:
        raise ValueError('actionable preparation requires pre_roll_s3 and zero native settling')
    return settings


def compact(env, info, action):
    result = train_timing.timing_compact(env, info, action)
    if 'actionable_preparation' in info:
        result['actionable_preparation'] = copy.deepcopy(info['actionable_preparation'])
    return result


def native_environment(spec, worker_id):
    import isaacgym
    import numpy as np
    import torch
    # Bind the original logger before installing our wrapper in a fresh spawn.
    from guitar_learning.skills.specialist_parallel import specialist_compact
    from guitar_learning.training import parallel
    from guitar_learning.quality.actionable_preparation_environment import build_environment
    from guitar_learning.timing.timing_curriculum import TimingConfig
    if not spec.get('headless', True):
        raise ValueError('actionable preparation training requires headless native sessions')
    seed = int(spec.get('seed', 7))+worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.set_num_threads(1)
    parallel._compact = compact
    return build_environment(spec['config'], Path(spec['out'])/'environment',
        role=spec['specialist']['role'], bundle=spec['bundle'], timing=TimingConfig(**spec['timing']),
        stage=spec['stage'], start_event_index=spec.get('start_event_index', 0),
        phrase_events=spec.get('phrase_events', 8), tempo_scale=spec.get('tempo_scale', 1.),
        seed=int(spec.get('seed', 7)), worker_id=worker_id, music=spec.get('music'),
        **dict(spec.get('env_kwargs', {})))


def preparation_summary(out):
    from guitar_learning.training.recording import write
    from guitar_learning.training.training_reports import run_evidence
    out = Path(out)
    evidence = run_evidence(out)
    result = dict(schema='guitar_learning.actionable_preparation_report.v2',
        policy_control_from_reset=True, native_settling_s=0., converted_preparation_s=2.,
        policy_horizon_s=7., **evidence['preparation'], accounting=evidence['accounting'],
        evidence_source=evidence['evidence_source'],
        scope='preparation actions and all native costs are included in ordinary PPO transitions; no readiness-based delay of score')
    write(out/'actionable_preparation_report.json', result)
    return result


def run(settings, args):
    import isaacgym
    from guitar_learning.timing import timing_transfer
    from guitar_learning.quality.actionable_preparation_transfer import apply_actor_initialization
    existed = args.out.exists()
    try:
        with patch.object(train_timing, 'timing_native_environment', native_environment), \
                patch.object(timing_transfer, 'apply_actor_initialization', apply_actor_initialization):
            return train_timing.run(settings, args)
    finally:
        if not existed and (args.out/'report.json').is_file():
            from guitar_learning.training.training_reports import finalize_summary
            finalize_summary(args.out, preparation_summary, 'actionable_preparation')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    run(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__': main()
