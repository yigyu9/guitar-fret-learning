"""PPO refinement of one fixed native skill after an explicit BC actor transfer."""
import argparse
import copy
import json
from pathlib import Path
import random


def settings_document(value):
    from guitar_learning.skills.skill_settings import settings_document as skill_settings
    from guitar_learning.imitation.imitation_environment import profile_settings
    if not isinstance(value, dict):
        raise ValueError('settings object required')
    value = copy.deepcopy(value)
    initialization = value.pop('actor_initialization', None)
    if (not isinstance(initialization, str) or not initialization or
            not Path(initialization).is_absolute() or not Path(initialization).is_file()):
        raise ValueError('existing absolute actor_initialization path required')
    stage = value.get('specialist')
    if isinstance(stage, dict) and any(stage.get(hand+'_checkpoint') is not None
                                      for hand in ('left', 'right')):
        raise ValueError('imitation PPO does not accept legacy expert checkpoints')
    settings = skill_settings(value)
    profile_settings(settings['specialist']['role'], settings['skill'])
    if settings['start_event_index'] != 0 or settings['tempo_scale'] != 1.:
        raise ValueError('imitation PPO requires first original event at tempo 1')
    settings['actor_initialization'] = str(Path(initialization).resolve())
    return settings


def imitation_native_environment(spec, worker_id):
    import isaacgym  # Must precede NumPy/Torch in each spawned native worker.
    import numpy as np
    import torch
    from guitar_learning.training import parallel
    from guitar_learning.imitation.imitation_environment import build_environment
    from guitar_learning.skills.specialist_parallel import specialist_compact
    if not spec.get('headless', True):
        raise ValueError('imitation PPO requires headless sessions')
    seed = int(spec.get('seed', 7))+worker_id
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    torch.set_num_threads(1)
    parallel._compact = specialist_compact
    return build_environment(spec['config'], Path(spec['out'])/'environment',
        role=spec['specialist']['role'], skill=spec['skill'],
        bundle=spec['bundle'], stage=spec['stage'],
        start_event_index=spec.get('start_event_index', 0),
        phrase_events=spec.get('phrase_events', 8), tempo_scale=spec.get('tempo_scale', 1.),
        seed=int(spec.get('seed', 7)), worker_id=worker_id,
        music=spec.get('music'), **dict(spec.get('env_kwargs', {})))


def run(settings, args):
    import isaacgym
    from unittest.mock import patch
    from guitar_learning.training import ppo
    from guitar_learning.skills import skill_parallel_v2
    from guitar_learning.tool.training import train_skills_v2
    from guitar_learning.imitation.imitation import apply_actor_initialization
    from guitar_learning.training.recording import digest, write
    from guitar_learning.native.lower_body_release_v1 import common
    initialization = Path(settings['actor_initialization']).resolve()
    expected_sha = digest(initialization)
    original_pin, original_trainer = common.pin, ppo.PPOTrainer
    original_pool = skill_parallel_v2.SkillPool

    def pin_with_initialization(config, extra=()):
        result = original_pin(config, extra=set(extra) | {initialization})
        if result.get(str(initialization)) != expected_sha:
            raise RuntimeError('BC actor initialization changed before run pin')
        return result

    class InitializingTrainer(original_trainer):
        def __init__(self, model, config=None):
            transfer = None
            if args.resume is None:
                if digest(initialization) != expected_sha:
                    raise RuntimeError('BC actor initialization changed before transfer')
                transfer = apply_actor_initialization(model, initialization)
            super().__init__(model, config)
            write(args.out.resolve()/'actor_initialization.json', dict(
                mode='strict_resume' if args.resume else 'BC_actor_only_new_critics_and_optimizers',
                path=str(initialization), sha256=expected_sha, transfer=transfer,
                strict_resume=str(args.resume.resolve()) if args.resume else None))

    class ConfiguredPool(original_pool):
        def __init__(self, *pool_args, **kwargs):
            super().__init__(*pool_args, worker_factory=imitation_native_environment, **kwargs)

    with patch.object(skill_parallel_v2, 'SkillPool', ConfiguredPool), \
         patch.object(ppo, 'PPOTrainer', InitializingTrainer), \
         patch.object(common, 'pin', pin_with_initialization):
        return train_skills_v2.run(settings, args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    import os
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    import isaacgym
    settings = settings_document(json.loads(args.settings.read_text()))
    run(settings, args)


if __name__ == '__main__': main()
