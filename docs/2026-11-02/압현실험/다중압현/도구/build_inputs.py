"""Generate explicit simultaneous diagnostic tasks; no song/strum compilation.

These new inputs require a future diagnostic runner. They are not substituted
for a sealed song bundle, and do not bypass any existing runtime input gate.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from inputs import ROOT, STUDY, imported_pins, merge_pins, sha, verify, write
sys.path.insert(0, str(ROOT))
from guitar_learning.song.task import ScoreTask, ScoreTarget


def make_diagnostic_task(case):
    rows = case['targets']
    if (len(rows) != 2 or len({r['finger_id'] for r in rows}) != 2 or
            len({r['string'] for r in rows}) != 2 or
            any(r['finger_id'] not in (1, 2, 3, 4) or not 1 <= r['fret'] <= 14 for r in rows)):
        raise ValueError('Two different strings/fingers and frets1..14 required')
    return ScoreTask(tuple(ScoreTarget(r['target_id'], case['case_id'], r['string'], r['fret'],
                           r['finger_id'], 1, 3., 4.5, 0., 0., 1.5) for r in rows))


def build(out):
    out = Path(out).resolve(); out.relative_to(STUDY)
    out.mkdir(parents=True, exist_ok=False)
    cases_path = STUDY/'설계/cases.json'
    pins = imported_pins(); merge_pins(pins, {str(cases_path): sha(cases_path)})
    protected = json.loads((STUDY/'입력/protected_sha256.json').read_text()); verify(protected)
    rows = []
    for case in json.loads(cases_path.read_text())['cases']:
        task = make_diagnostic_task(case)
        targets = [asdict(t) for t in task.targets]
        decoded = ScoreTask(tuple(ScoreTarget(**r) for r in json.loads(json.dumps(targets))))
        if decoded.targets != task.targets:
            raise ValueError('Diagnostic target round-trip mismatch')
        path = out/(case['case_id']+'.json')
        write(path, dict(schema='multi_press.diagnostic_task.v1', case_id=case['case_id'],
            targets=targets, audible_window_s=[3., 4.5], planned_episode_duration_s=5.,
            string_convention='runtime0=high-e,5=low-E', source_sha256=pins,
            native_runner_validated=False, song_bundle_compatible=False,
            scope='Explicit new two-finger diagnostic contract. No inherited song/native success.'))
        rows.append(dict(case_id=case['case_id'], task=str(path), sha256=sha(path), target_count=2))
    merge_pins(pins, imported_pins()); verify(pins); verify(protected)
    write(out/'report.json', dict(completed=True, rows=rows, source_sha256=pins,
          protected_inputs_unchanged=True, physical_tests=0, native_runner_validated=False))
    print(json.dumps(dict(completed=True, cases=len(rows), target_count_each=2)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    build(args.out)
