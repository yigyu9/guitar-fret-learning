"""Train hand-internal stages with observable objective history and native safety."""
import argparse
import json
from pathlib import Path


def run(settings, args):
    from unittest.mock import patch
    from guitar_learning.skills import skill_parallel
    from guitar_learning.tool.training import train_skills
    from guitar_learning.skills.skill_parallel_v2 import SkillPool
    with patch.object(skill_parallel, 'SkillPool', SkillPool):
        return train_skills.run(settings, args)


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
    from guitar_learning.skills.skill_settings import settings_document
    settings = settings_document(json.loads(args.settings.read_text()))
    run(settings, args)


if __name__ == '__main__': main()
