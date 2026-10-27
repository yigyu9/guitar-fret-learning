"""Train measured fretting/strike quality with unchanged native support."""
import argparse
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch
from guitar_learning.tool.training import train_actionable_preparation as previous
from guitar_learning.quality.runtime import compact, native_environment, summarize_run


def settings_document(raw):
    from guitar_learning.quality.musical_quality import metadata
    value = copy.deepcopy(raw)
    declared = value.pop('musical_quality', None)
    if declared is not None and declared != metadata():
        raise ValueError('known musical quality contract required')
    result = previous.settings_document(value)
    if result['actor_initialization_kind'] != 'ppo':
        raise ValueError('musical quality requires own actionable PPO actor initialization')
    result['musical_quality'] = metadata()
    return result


def run(settings, args):
    from guitar_learning.quality import actionable_preparation_transfer
    from guitar_learning.quality.musical_quality_transfer import apply_actor_initialization
    existed = args.out.exists()
    try:
        with patch.object(previous, 'native_environment', native_environment), \
                patch.object(actionable_preparation_transfer, 'apply_actor_initialization', apply_actor_initialization):
            return previous.run(settings, args)
    finally:
        if not existed and (args.out/'report.json').is_file():
            from guitar_learning.training.training_reports import finalize_summary
            finalize_summary(args.out, summarize_run, 'musical_quality')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', type=Path)
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'): os.environ[name] = '1'
    import isaacgym
    run(settings_document(json.loads(args.settings.read_text())), args)


if __name__ == '__main__': main()
