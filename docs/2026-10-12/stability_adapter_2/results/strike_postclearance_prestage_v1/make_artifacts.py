#!/usr/bin/env python3
"""Validate saved post-clearance prestage data and copy selected native PNGs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE / 'native/data'
ANALYSIS = HERE / 'analysis'
CAPTURE = NATIVE / 'images/capture.json'
SELECTED = {0: '0.000 s initial', 320: '1.333 s', 784: '3.267 s prestage begins', 1200: '5.000 s final PLAY'}
RECOVERY_TIMES = [91 / 60, 1.8, 2.65, 3.25, 3.966666666666667, 4.666666666666667]


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def scalar(value):
    return value[0] if isinstance(value, list) and value else value


def main():
    report_path = NATIVE / 'report.json'
    controls_path = NATIVE / 'controls.json'
    trace_path = NATIVE / 'trace.json'
    initial_path = NATIVE / 'initial_values.json'
    connection_path = NATIVE / 'checkpoint_connection.json'
    pd_path = NATIVE / 'PD_phase_properties.json'
    videos_path = NATIVE / 'images/videos.json'
    native_before_path = HERE / 'native/inputs_before.json'
    native_after_path = HERE / 'native/inputs_after.json'
    summary_path = ANALYSIS / 'summary.json'
    analysis_before_path = ANALYSIS / 'inputs_before.json'
    analysis_after_path = ANALYSIS / 'inputs_after.json'
    source_path = Path('/home/ajou/yigyu/3/stability_adapter_2/run_strike_postclearance_prestage.py')
    preserved_path = Path('/home/ajou/yigyu/3/stability_adapter_2/strike_postclearance_prestage_preserved_run.py')
    analyzer_path = Path('/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_transfer_trials_v2.py')
    producer_path = Path(__file__).resolve()
    stable_files = [report_path, controls_path, trace_path, initial_path, connection_path,
                    pd_path, CAPTURE, videos_path, native_before_path, native_after_path,
                    summary_path, analysis_before_path, analysis_after_path,
                    source_path, preserved_path, analyzer_path, producer_path]
    before = {str(p): sha(p) for p in stable_files}

    report = load(report_path)
    controls = load(controls_path)
    trace = load(trace_path)
    native_before = load(native_before_path)
    native_after = load(native_after_path)
    analysis_before = load(analysis_before_path)
    analysis_after = load(analysis_after_path)
    summary = load(summary_path)['trials'][0]
    capture = load(CAPTURE)
    assert report['completed_5s'] and report['physics_steps'] == 1200 and report['frame_count'] == 151
    assert len(report['checks']) == 28 and all(report['checks'].values())
    assert native_after['inputs_unchanged'] and native_after['input_count'] == 1115
    assert len(native_before['sha256']) == 1115
    assert analysis_after['unchanged'] and len(analysis_before['sha256']) == 7
    assert len(controls) == 300 and len(trace) == 151
    assert summary['phase_control_counts'] == {'PREPARE': 49, 'PLAY': 251, 'HOLD': 0}
    assert summary['source_pulse_totals'] == {'target_hit': 4.0, 'physical_target_hit': 6.0,
            'physical_release': 7.0, 'miss': 6.0, 'wrong_crossing_count': 1.0}
    assert summary['accepted_release_mask_total'] == 6.0
    assert summary['source_terminal_time_s'] is None
    assert report['phase_end'] == 'PLAY' and report['stop_reason'] is None
    assert report['terminal_PD_baseline_restored'] is False
    assert summary['max_rotation_change_deg'] == 7.095454906376965
    assert summary['end_rotation_change_deg'] == 3.3525459932698047

    recovery_times = []
    for row in controls:
        info = row.get('info', {})
        if scalar(info.get('scheduled_recovery_complete_pulse')):
            recovery_times.append(float(row['time_s']))
    if len(recovery_times) != 6 or any(abs(a-b) > 1e-9 for a, b in zip(recovery_times, RECOVERY_TIMES)):
        raise RuntimeError('saved scheduled recovery pulses differ from expected raw times: {}'.format(recovery_times))
    active_rows = []
    for row in controls:
        prestage = row.get('phase_target_residual', {}).get('postclearance_prestage', {})
        if prestage.get('active'):
            active_rows.append(row)
    assert len(active_rows) == 6
    assert abs(float(active_rows[0]['time_s']) - 3.2666666666666666) < 1e-9
    assert all(r['phase_target_residual']['postclearance_prestage']['source_motor_phase'] == 2 for r in active_rows)
    right_noncontact = sum(bool(row.get('readiness', {}).get('conditions', {}).get('right_noncontact')) for row in controls if row['phase'] == 'PLAY')
    assert right_noncontact == 251

    frames = {int(r['physics_step']): r for r in capture['frames']}
    assert len(capture['frames']) == 151
    out = HERE / 'artifacts'
    out.mkdir(exist_ok=True)
    chosen = []
    for step, caption in SELECTED.items():
        if step not in frames:
            raise RuntimeError('selected camera frame absent: {}'.format(step))
        frame = frames[step]
        whole = Path(next(p for p in frame['image_sha256'] if '/whole_body/' in p))
        hands = Path(next(p for p in frame['image_sha256'] if '/hands/' in p))
        for camera, src in [('whole_body', whole), ('hands', hands)]:
            expected = frame['image_sha256'][str(src)]
            actual = sha(src)
            if actual != expected:
                raise RuntimeError('native capture SHA mismatch: {}'.format(src))
            dst = out / '{}_{:05d}.png'.format(camera, step // 8)
            dst.write_bytes(src.read_bytes())
            copied = sha(dst)
            if copied != actual or sha(src) != actual:
                raise RuntimeError('image byte-copy mismatch: {}'.format(dst))
            chosen.append({'camera': camera, 'physics_step': step, 'time_s': frame['time_s'],
                           'caption': caption, 'source': str(src), 'copy': str(dst),
                           'sha256_source_before': actual, 'sha256_copy': copied,
                           'sha256_source_after': sha(src)})
    after = {str(p): sha(p) for p in stable_files}
    if before != after:
        raise RuntimeError('saved raw/producer/helper/source/analyzer SHA changed')
    manifest = {
        'producer': str(producer_path),
        'producer_scope': 'saved-data checks and byte-exact copies of native PNGs; no native initialization or simulation',
        'source_sha256_before': before,
        'source_sha256_after': after,
        'source_sha256_unchanged': before == after,
        'native_report': {'physics_steps': report['physics_steps'], 'camera_frames': report['frame_count'],
                          'checks_passed': len(report['checks']), 'native_input_count': native_after['input_count']},
        'analysis_input_count': len(analysis_before['sha256']),
        'trace_rows': len(trace),
        'scheduled_recovery_times_s': recovery_times,
        'prestage_active_commands': len(active_rows),
        'right_noncontact_PLAY_rows': right_noncontact,
        'selected_native_frames': chosen,
    }
    (out / 'artifact_manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'copied_native_pngs': len(chosen), 'source_sha_unchanged': True,
                      'native_closure': native_after['input_count'], 'analysis_sha_count': len(analysis_before['sha256']),
                      'scheduled_recovery_times_s': recovery_times}, indent=2))


if __name__ == '__main__':
    main()
