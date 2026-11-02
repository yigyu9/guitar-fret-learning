"""Read-only snapshot of the ongoing single-target study; no native imports."""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import sys

STUDY = Path(__file__).resolve().parents[1]
ROOT = next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
SINGLE = STUDY.parent/'단일압현/전수검증_1-14_v1'
FINGERS = ('index', 'middle', 'ring', 'pinky')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path = Path(path).resolve()
    path.relative_to(STUDY)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    with path.open('x', encoding='utf-8') as stream:
        stream.write(payload)


def resolve(path):
    path = Path(path)
    path = (path if path.is_absolute() else ROOT/path).resolve()
    path.relative_to(ROOT)
    return path


def verify(pins):
    if not pins:
        raise ValueError('Nonempty source pins required')
    changed = [str(p) for name, expected in pins.items()
               for p in [resolve(name)] if not p.is_file() or sha(p) != expected]
    if changed:
        raise ValueError('Input integrity mismatch: '+repr(changed))


def merge_pins(pins, additional):
    """Never replace an earlier expectation with the current file hash."""
    for name, value in additional.items():
        if name in pins and pins[name] != value:
            raise ValueError('Input changed during run: '+name)
        pins.setdefault(name, value)


def imported_pins():
    """Include actually imported active project modules, never archived code."""
    result = {}
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if not name or not name.endswith('.py'):
            continue
        path = Path(name).resolve()
        try:
            path.relative_to(ROOT/'guitar_learning')
        except ValueError:
            continue
        else:
            if 'archive' in path.parts:
                raise ValueError('Archived Python import forbidden: '+str(path))
            result[str(path)] = sha(path)
    for path in (STUDY/'도구').glob('*.py'):
        result[str(path)] = sha(path)
    return result


def prepare():
    manifest_path = SINGLE/'로그/sweep_v1/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    frozen = SINGLE/'로그/sweep_v1/geometry_frozen.json'
    geometry = json.loads(frozen.read_text())
    protected = {str(resolve(k)): v for d in (manifest['pins'], geometry['source_sha256'])
                 for k, v in d.items()}
    protected[str(manifest_path)] = sha(manifest_path)
    if sha(frozen) != manifest['source_geometry_sha256']:
        raise ValueError('Frozen geometry identity mismatch')
    verify(protected)
    state_path = SINGLE/'로그/sweep_v1/state.json'
    raw = state_path.read_bytes()
    state = json.loads(raw)
    if state['manifest_sha256'] != sha(manifest_path):
        raise ValueError('Single-study state identity mismatch')
    evidence = {}
    for identity, row in state['results'].items():
        if row.get('status') != 'done':
            continue
        path = resolve(row['report'])
        report = json.loads(path.read_text())
        required = ('completed', 'execution_completed', 'source_sha256_match_after',
                    'scene_closed', 'pool_closed')
        if (report.get('case') != identity or report.get('failure') is not None or
                not all(report.get(k) is True for k in required)):
            raise ValueError('Invalid completed single report: '+identity)
        pins = json.loads((path.parent/'inputs_before.json').read_text())
        verify(pins)
        evidence[identity] = dict(outcome=report['outcome'], report=str(path), sha256=sha(path))
    # Representative ordering declared before the new CPU search.
    pairs = [
        ('same', ('ring', 2, 12), ('pinky', 1, 12)),
        ('same', ('ring', 3, 12), ('pinky', 2, 12)),
        ('same', ('ring', 4, 12), ('pinky', 3, 12)),
        ('same', ('middle', 1, 12), ('ring', 2, 12)),
        ('adjacent', ('ring', 2, 11), ('pinky', 1, 12)),
        ('adjacent', ('middle', 1, 12), ('ring', 2, 13)),
        ('gap', ('ring', 3, 10), ('pinky', 2, 12)),
        ('gap', ('index', 4, 10), ('ring', 3, 12)),
    ]
    cases = []
    for i, (stage, *targets) in enumerate(pairs, 1):
        rows = []
        for finger, string, fret in targets:
            identity = f'{finger}_s{string}_f{fret}'
            rows.append(dict(target_id=identity, finger=finger, finger_id=FINGERS.index(finger)+1,
                             string=string-1, string_standard_1based=string, fret=fret,
                             single_evidence=evidence.get(identity, dict(outcome='not_verified_at_snapshot'))))
        cases.append(dict(case_id=f'pair{i:02d}_{stage}', stage=stage, targets=rows,
                          native_verified=False))
    stamp = datetime.now(timezone(timedelta(hours=9))).isoformat()
    write(STUDY/'입력/single_snapshot.json', dict(captured_kst=stamp, source=str(state_path),
          source_sha256=hashlib.sha256(raw).hexdigest(), state=state, evidence=evidence))
    write(STUDY/'입력/protected_sha256.json', protected)
    write(STUDY/'설계/cases.json', dict(schema='multi_press.cases.v1', total=8,
          string_convention='standard 1=high-e; runtime string=standard-1; mapping builder uses reverse order',
          audible_window_s=[3., 4.5], cases=cases, original_success_inherited=False))
    print(json.dumps(dict(captured_kst=stamp, finished=state['finished'], remaining=state['remaining'],
                          protected_files=len(protected), cases=len(cases))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'verify'])
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare()
    else:
        pins = json.loads((STUDY/'입력/protected_sha256.json').read_text())
        verify(pins)
        print(json.dumps(dict(protected_files=len(pins), all_match=True)))
