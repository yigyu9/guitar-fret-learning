#!/usr/bin/env python3
"""Copy selected native camera stills and verify saved-data provenance; no simulation."""
import hashlib
import json
import shutil
from pathlib import Path

PHASE = Path(__file__).resolve().parent
ROOT = Path('/home/ajou/yigyu/3')
SOURCE_ROOT = ROOT / 'stability_adapter_2'
NATIVE = PHASE / 'native'
DATA = NATIVE / 'data'
IMAGE_DIR = DATA / 'images'
OUT = PHASE / 'artifacts'

JSON_INPUTS = [
    NATIVE / 'data/report.json',
    PHASE / 'analysis/summary.json',
    DATA / 'controls.json',
    DATA / 'trace.json',
    DATA / 'initial_values.json',
    DATA / 'checkpoint_connection.json',
    IMAGE_DIR / 'capture.json',
    IMAGE_DIR / 'videos.json',
    NATIVE / 'inputs_before.json',
    NATIVE / 'inputs_after.json',
    PHASE / 'analysis/inputs_before.json',
    PHASE / 'analysis/inputs_after.json',
    PHASE / 'lateral_staging_audit.json',
]
SOURCE_INPUTS = [
    SOURCE_ROOT / 'run_strike_lateral_staging.py',
    PHASE / 'audit_lateral_staging.py',
    Path(__file__).resolve(),
]
FRAME_STEPS = (0, 320, 816, 1200)
CAMERAS = ('whole_body', 'hands')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    inputs = JSON_INPUTS + SOURCE_INPUTS
    before = {str(p): sha256(p) for p in inputs}
    data = {str(p): json.loads(p.read_text()) for p in JSON_INPUTS}
    report = data[str(DATA / 'report.json')]
    trial = data[str(PHASE / 'analysis/summary.json')]['trials'][0]
    native_after = data[str(NATIVE / 'inputs_after.json')]
    analysis_after = data[str(PHASE / 'analysis/inputs_after.json')]
    trace = data[str(DATA / 'trace.json')]
    capture = data[str(IMAGE_DIR / 'capture.json')]

    assert report['completed_5s'] and report['physics_steps'] == 1200 and report['frame_count'] == 151
    assert len(report['checks']) == 27 and all(report['checks'].values())
    assert native_after['inputs_unchanged'] and native_after['input_count'] == 1109
    assert trial['closure']['inputs_unchanged'] and trial['closure']['input_count'] == 1109
    assert analysis_after['unchanged'] and len(data[str(PHASE / 'analysis/inputs_before.json')]['sha256']) == 7
    assert len(trace) == 151 and trace[-1]['physics_step'] == 1200 and trace[-1]['phase'] == 'PLAY'
    assert not any(row['phase'] == 'HOLD' for row in trace)
    assert sum(row['phase'] == 'PREPARE' for row in trace) == 25
    assert report['phase_end'] == 'PLAY' and report['stop_reason'] is None
    assert report['music_success'] is False and report['learning_updates'] == 0

    frames_by_step = {row['physics_step']: row for row in capture['frames']}
    OUT.mkdir(parents=True, exist_ok=True)
    copied = []
    for step in FRAME_STEPS:
        frame = frames_by_step[step]
        for camera in CAMERAS:
            source = Path(next(p for p in frame['image_sha256'] if '/{}/'.format(camera) in p))
            expected = frame['image_sha256'][str(source)]
            if sha256(source) != expected:
                raise RuntimeError('Native image SHA mismatch: {}'.format(source))
            target = OUT / '{}_{:05d}.png'.format(camera, int(round(frame['time_s'] * 30)))
            shutil.copyfile(source, target)
            source_sha = sha256(source)
            copy_sha = sha256(target)
            if source_sha != expected or copy_sha != expected:
                raise RuntimeError('Copied image SHA mismatch: {}'.format(target))
            copied.append({
                'camera': camera, 'physics_step': step, 'time_s': frame['time_s'],
                'source': str(source), 'copy': str(target),
                'sha256_source_before': expected, 'sha256_copy': copy_sha,
                'sha256_source_after': source_sha,
            })

    after = {str(p): sha256(p) for p in inputs}
    if before != after:
        raise RuntimeError('Consumed source/input SHA changed while producing artifacts')
    manifest = {
        'producer': str(Path(__file__).resolve()),
        'producer_scope': 'saved-data validation and byte-exact copy of native PNGs; no native initialization, physics, or re-encoding',
        'source_sha256_before': before,
        'source_sha256_after': after,
        'source_sha256_unchanged': before == after,
        'native_report': {
            'physics_steps': report['physics_steps'], 'camera_frames': report['frame_count'],
            'checks_passed': sum(bool(v) for v in report['checks'].values()),
            'native_input_count': native_after['input_count'],
        },
        'analysis_input_count': len(data[str(PHASE / 'analysis/inputs_before.json')]['sha256']),
        'selected_native_frames': copied,
    }
    (OUT / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'selected_frames': len(copied), 'source_sha_unchanged': before == after,
                      'manifest': str(OUT / 'artifact_manifest.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
