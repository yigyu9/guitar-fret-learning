"""Prepare reviewed-input candidates only; this tool never seals or starts jobs."""
import argparse
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parents[1]
BASE = STUDY.parent/'학습_인접2지_v1'
sys.path.insert(0, str(BASE/'도구'))
from prepare import load_cases, make_settings, verify_pins, sha
from study_queue_v2 import GPU_UUID, SINGLE, verify_manifest as verify_baseline
from guitar_learning.portability import portable, settings_digest

CONDITION = dict(schema='multi_press.target_approach_condition.v3', condition='B2',
    natural_preparation=dict(schema='guitar_learning.natural_preparation.v3', condition='E4'),
    initialization='fresh', teacher=None)
BASELINE_MANIFEST = BASE/'설계/after_parallel_hold_v1.json'
BASELINE_STATE = BASE/'로그/queue_after_parallel_v1/state.json'


def improved_settings():
    case = next(c for c in load_cases() if c['case_id'] == 'index_middle_same')
    bundle = BASE/'입력/song_bundles/index_middle_same'
    settings = make_settings(case, bundle, updates=100, num_envs=64, horizon=32,
                             size='medium', seed=7)
    settings['experiment']['improvement'] = json.loads(json.dumps(CONDITION))
    return settings


def write_new(path, value):
    path = Path(path).resolve(); path.relative_to(STUDY)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def prepare_draft(out):
    out = Path(out).resolve(); out.relative_to(STUDY)
    parent = verify_baseline(BASELINE_MANIFEST)
    settings = improved_settings()
    settings_path = out/'B2_index_middle_same_settings.json'
    write_new(settings_path, portable(settings))
    pins = dict(parent['pins'])
    pins[str(BASELINE_MANIFEST)] = sha(BASELINE_MANIFEST)
    for path in (STUDY/'도구').rglob('*.py'):
        pins[str(path)] = sha(path)
    pins[str(settings_path)] = sha(settings_path)
    verify_pins(pins)
    train = dict(job_id='B2_index_middle_same_train', mode='train', case_id='index_middle_same',
        bundle=str(BASE/'입력/song_bundles/index_middle_same'),
        updates=100, num_envs=64, horizon=32, seed=7, size='medium',
        out=str(STUDY/'로그/B2/training'), settings=str(settings_path),
        settings_sha256=settings_digest(settings))
    evaluate = dict(job_id='B2_index_middle_same_evaluate', mode='evaluate',
        case_id=train['case_id'], bundle=train['bundle'], train_job_id=train['job_id'],
        checkpoint=str(Path(train['out'])/'J/final.pt'), out=str(STUDY/'로그/B2/evaluation'))
    candidate = dict(schema='multi_press.target_approach_training.v3', sealed=False,
        condition=CONDITION, python=parent['python'], gpu_uuid=GPU_UUID, single_state=str(SINGLE),
        baseline_manifest=str(BASELINE_MANIFEST), baseline_state=str(BASELINE_STATE),
        common_window_s=[3.3, 4.8], train_transitions=204800,
        evaluation_first_episode_denominator=32, automatic_retry=False,
        baseline_case='index_middle_same', baseline_comparison='B0 same64/H32/100/seed7 only',
        pins=pins, jobs=[train, evaluate])
    path = out/'training_manifest_draft.json'
    write_new(path, dict(schema='multi_press.target_approach_training_draft.v3',
        executable=False, instruction='Independent review and root sealing required; do not run this draft',
        candidate=candidate))
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=STUDY/'설계/B2')
    print(prepare_draft(parser.parse_args().out))
