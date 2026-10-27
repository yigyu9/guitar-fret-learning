#!/usr/bin/env python3
"""Validate saved lateral-latch artifacts and byte-copy selected native PNGs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native/data'
ANALYSIS = HERE / 'analysis'
CAPTURE = NATIVE / 'images/capture.json'
SELECTED = {0: '0.000 s initial', 320: '1.333 s early hit', 824: '3.433 s latch divergence', 1200: '5.000 s final HOLD'}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def main():
    report_path = NATIVE / 'report.json'
    controls_path = NATIVE / 'controls.json'
    trace_path = NATIVE / 'trace.json'
    initial_path = NATIVE / 'initial_values.json'
    connection_path = NATIVE / 'checkpoint_connection.json'
    videos_path = NATIVE / 'images/videos.json'
    native_before_path = HERE / 'native/inputs_before.json'
    native_after_path = HERE / 'native/inputs_after.json'
    analysis_summary_path = ANALYSIS / 'summary.json'
    analysis_before_path = ANALYSIS / 'inputs_before.json'
    analysis_after_path = ANALYSIS / 'inputs_after.json'
    audit_path = HERE / 'lateral_latch_audit.json'
    source_path = Path('/home/ajou/yigyu/3/stability_adapter_2/run_strike_lateral_latch.py')
    helper_path = HERE / 'audit_lateral_latch.py'
    producer_path = Path(__file__).resolve()
    stable_files = [report_path, controls_path, trace_path, initial_path, connection_path,
                    CAPTURE, videos_path, native_before_path, native_after_path,
                    analysis_summary_path, analysis_before_path, analysis_after_path,
                    audit_path, source_path, helper_path, producer_path]
    before = {str(p): sha(p) for p in stable_files}

    report = load(report_path)
    controls = load(controls_path)
    trace = load(trace_path)
    native_before = load(native_before_path)
    native_after = load(native_after_path)
    analysis_before = load(analysis_before_path)
    analysis_after = load(analysis_after_path)
    summary = load(analysis_summary_path)['trials'][0]
    audit = load(audit_path)
    capture = load(CAPTURE)

    assert report['completed_5s'] and report['physics_steps'] == 1200 and report['frame_count'] == 151
    assert report['phase_end'] == 'HOLD' and report['stop_reason'] == 'source_terminal'
    assert len(report['checks']) == 27 and all(report['checks'].values())
    assert native_after['inputs_unchanged'] and native_after['input_count'] == 1112
    assert len(native_before['sha256']) == 1112
    assert analysis_after['unchanged'] and len(analysis_before['sha256']) == 7
    assert len(controls) == 300 and len(trace) == 152
    assert sum(r['phase'] == 'PREPARE' for r in controls) == 49
    assert sum(r['phase'] == 'PLAY' for r in controls) == 180
    assert sum(r['phase'] == 'HOLD' for r in controls) == 71
    assert sum(r['phase'] == 'HOLD' for r in trace) == 37
    assert trace[-1]['physics_step'] == 1200 and trace[-1]['time_s'] == 5.0 and trace[-1]['phase'] == 'HOLD'
    terminal_rows = [r for r in trace if r['physics_step'] == 916]
    assert len(terminal_rows) == 1 and terminal_rows[0]['time_s'] == 916 / 240 and terminal_rows[0]['phase'] == 'HOLD'
    assert summary['phase_control_counts'] == {'PREPARE': 49, 'PLAY': 180, 'HOLD': 71}
    assert summary['source_pulse_totals'] == {'target_hit': 4.0, 'physical_target_hit': 4.0,
            'physical_release': 8.0, 'miss': 4.0, 'wrong_crossing_count': 4.0}
    assert summary['accepted_release_mask_total'] == 4.0 and summary['source_terminal_time_s'] == 916 / 240
    assert audit['inputs_unchanged'] and audit['native_manifest_input_count'] == 1112
    assert audit['commonfield_control_prefix_exact_count'] == 206 and audit['native_trace_prefix_exact_count'] == 104
    assert audit['terminal_HOLD_count'] == 71 and audit['terminal_PD_restore_native_readback_baseline_exact']

    frames = {int(r['physics_step']): r for r in capture['frames']}
    if len(capture['frames']) != 151:
        raise RuntimeError('capture frame count differs from native report')
    out = HERE / 'artifacts'
    out.mkdir(exist_ok=True)
    chosen = []
    for step, caption in SELECTED.items():
        if step not in frames:
            raise RuntimeError('selected camera frame absent: {}'.format(step))
        frame = frames[step]
        src_whole = Path(next(p for p in frame['image_sha256'] if '/whole_body/' in p))
        src_hands = Path(next(p for p in frame['image_sha256'] if '/hands/' in p))
        for camera, src in [('whole_body', src_whole), ('hands', src_hands)]:
            expected = frame['image_sha256'][str(src)]
            actual = sha(src)
            if actual != expected:
                raise RuntimeError('capture source SHA mismatch: {}'.format(src))
            dst = out / '{}_{:05d}.png'.format(camera, step // 8)
            dst.write_bytes(src.read_bytes())
            copied = sha(dst)
            if copied != actual or sha(src) != actual:
                raise RuntimeError('byte-copy verification failed: {}'.format(dst))
            chosen.append({'camera': camera, 'physics_step': step, 'time_s': frame['time_s'],
                           'caption': caption, 'source': str(src), 'copy': str(dst),
                           'sha256_source_before': actual, 'sha256_copy': copied,
                           'sha256_source_after': sha(src)})

    after = {str(p): sha(p) for p in stable_files}
    if before != after:
        raise RuntimeError('a saved input/source/helper/producer SHA changed during artifact production')
    manifest = {
        'producer': str(producer_path),
        'producer_scope': 'saved-data validation and byte-exact copy of selected native PNGs; no native initialization or simulation',
        'source_sha256_before': before,
        'source_sha256_after': after,
        'source_sha256_unchanged': before == after,
        'native_report': {'physics_steps': report['physics_steps'], 'camera_frames': report['frame_count'],
                          'checks_passed': sum(bool(v) for v in report['checks'].values()),
                          'native_input_count': native_after['input_count']},
        'analysis_input_count': len(analysis_before['sha256']),
        'trace_rows': len(trace),
        'trace_terminal_sample': {'physics_step': terminal_rows[0]['physics_step'],
                                  'time_s': terminal_rows[0]['time_s'], 'phase': terminal_rows[0]['phase'], 'off_grid_extra_sample': True},
        'selected_native_frames': chosen,
    }
    (out / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'copied_native_pngs': len(chosen), 'source_sha_unchanged': True,
                      'trace_rows': len(trace), 'camera_frames': len(capture['frames'])}, indent=2))


if __name__ == '__main__':
    main()
