"""Train explicit reach/contact/hold or ready/cross stages with native safety."""
import argparse
import json
from pathlib import Path


def summarize_run(out):
    from guitar_learning.training.recording import write
    out = Path(out)
    report = json.loads((out/'report.json').read_text())
    summary = json.loads((out/'specialist_report.json').read_text())
    skill = report['settings']['skill']
    summary['skill'] = skill
    summary['success_scope'] = ('preparation_geometry_only' if skill in ('reach', 'ready')
        else 'native_contact_candidate' if summary['role'] == 'left'
        else 'geometric_marker_crossing')
    summary['scope'] = ('Explicit hand-internal skill achievement after safe full horizon; '
        'reach/ready are preparation only; original joint music is unchanged; no pressure/sound certification')
    write(out/'skill_report.json', summary)
    return summary


def run(settings, args):
    from unittest.mock import patch
    from guitar_learning.skills import specialist_parallel
    from guitar_learning.tool.training import train_specialists
    from guitar_learning.skills.skill_parallel import SkillPool
    class SelectedSkillPool(SkillPool):
        def __init__(self, specs, **kwargs):
            super().__init__(specs, skill=settings['skill'], **kwargs)

    # The specialist runner imports its Pool at invocation time. Both bindings
    # last for the complete CLI run and are restored even on interruption.
    with patch.object(specialist_parallel, 'SpecialistPool',
                      SelectedSkillPool):
        train_specialists.run(settings, args)
    return summarize_run(args.out.resolve())


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


if __name__ == '__main__':
    main()
