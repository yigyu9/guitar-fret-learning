#!/usr/bin/env python3
"""Create a metadata-only v20 correction for two timed-entry video records."""
import ast
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2')
OUT = ROOT / 'results/video_collection_v20'
V19_MANIFEST = ROOT / 'video_manifest_v19.json'
V19_INDEX = ROOT / 'VIDEO_INDEX_v19.md'
PHASE = ROOT / 'results/strike_timed_entry_v1/native_retry_v1/data'
REPORT = PHASE / 'report.json'
CONTROLS = PHASE / 'controls.json'
TRACE = PHASE / 'trace.json'
SOURCE_PRODUCER = ROOT / 'results/video_collection_v19/collect_videos.py'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def assert_safe_ast(path):
    tree = ast.parse(path.read_text(), filename=str(path))
    forbidden_imports = {'subprocess', 'shutil', 'os', 'torch', 'isaacgym'}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else [(node.module or '').split('.')[0]]
            if forbidden_imports.intersection(names):
                raise RuntimeError('unsafe import in correction producer: {}'.format(names))
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ''
            if name in {'system', 'Popen', 'run', 'call', 'copyfile', 'copy2', 'move', 'unlink', 'remove'}:
                raise RuntimeError('unsafe call in correction producer: {}'.format(name))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    script_path = Path(__file__).resolve()
    assert_safe_ast(script_path)
    # This is an immutable metadata correction, not a collector rerun.
    source_paths = [V19_MANIFEST, V19_INDEX, REPORT, CONTROLS, TRACE, SOURCE_PRODUCER, script_path]
    before = {str(p): sha(p) for p in source_paths}
    manifest = load(V19_MANIFEST)
    report = load(REPORT)
    controls = load(CONTROLS)
    trace = load(TRACE)
    index = V19_INDEX.read_text()

    if report.get('phase_end') != 'HOLD' or report.get('stop_reason') != 'source_terminal':
        raise RuntimeError('unexpected timed-entry retry terminal metadata')
    hold_controls = [r for r in controls if r.get('phase') == 'HOLD']
    hold_trace = [r for r in trace if r.get('phase') == 'HOLD']
    if not hold_controls or not hold_trace:
        raise RuntimeError('saved control/trace has no HOLD continuation')
    first_hold_time = float(hold_controls[0]['time_s'])
    if any(r.get('phase') != 'HOLD' for r in controls[controls.index(hold_controls[0]):]):
        raise RuntimeError('HOLD controls are not a terminal suffix')
    if any(r.get('phase') != 'HOLD' for r in trace[trace.index(hold_trace[0]):]):
        raise RuntimeError('HOLD trace is not a terminal suffix')
    if first_hold_time != float(hold_trace[0]['time_s']):
        raise RuntimeError('control/trace first HOLD timestamps disagree')

    target_report = str(REPORT)
    update_count = 0
    for group in ('source_inventory', 'new_copies'):
        for row in manifest[group]:
            exp = row.get('experiment', {})
            if exp.get('phase') == 'strike_timed_entry_v1' and exp.get('report') == target_report:
                exp['terminal_time_s'] = first_hold_time
                exp['continued_in_hold'] = True
                exp['hold_control_count'] = len(hold_controls)
                exp['hold_trace_count'] = len(hold_trace)
                exp['hold_first_control_time_s'] = first_hold_time
                update_count += 1
    if update_count != 4:
        raise RuntimeError('expected exactly four duplicated experiment records, got {}'.format(update_count))
    manifest['version'] = 20
    manifest['corrected_from_version'] = 19
    manifest['metadata_only_correction'] = True
    manifest['new_video_copies_in_v20'] = 0
    manifest['correction_audit'] = {
        'source_report': str(REPORT),
        'source_controls': str(CONTROLS),
        'source_trace': str(TRACE),
        'phase_end': report['phase_end'],
        'stop_reason': report['stop_reason'],
        'first_hold_time_s': first_hold_time,
        'hold_control_rows': len(hold_controls),
        'hold_trace_rows': len(hold_trace),
        'v19_metadata_unchanged': True,
        'v19_manifest_sha256_before_after': before[str(V19_MANIFEST)],
        'v19_index_sha256_before_after': before[str(V19_INDEX)],
        'v19_collector_sha256_before_after': before[str(SOURCE_PRODUCER)],
        'archive_files_sha256_preserved': True,
        'archive_file_count': manifest['archive_count_after'],
        'v18_preserved_count': manifest['existing_v18_count_before'],
        'v19_added_copy_count': manifest['new_unique_copies'],
        'corrected_experiment_record_count': update_count,
    }

    # Correct only the two affected table cells while retaining all v19 links/table rows.
    index = index.replace('# Native video collection v19 — 266개', '# Native video collection v20 — 266개', 1)
    first_line_end = index.find('\n')
    index = index[:first_line_end + 1] + '\n> v20은 v19의 메타데이터 보정본이다. 영상 복사나 재수집은 없으며, 아래 timed-entry native_retry_v1 두 영상에서 저장된 HOLD 연속 실행을 raw controls/trace로 확인해 상태를 바로잡았다. 상세 대조는 [보정 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/video_collection_v20/README.md)와 [보정 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_manifest_v20.json)를 참조한다.\n' + index[first_line_end + 1:]
    corrected = 0
    rows = []
    for line in index.splitlines():
        if 'strike_timed_entry_v1/native_retry_v1/' in line and '| 아니오 |' in line:
            line = line.replace('| 아니오 |', '| 예 (HOLD 시작 {:.6f}초; controls {}행) |'.format(first_hold_time, len(hold_controls)), 1)
            corrected += 1
        rows.append(line)
    index = '\n'.join(rows) + '\n'
    if corrected != 2:
        raise RuntimeError('expected two affected index rows, got {}'.format(corrected))

    # Independently verify all 266 existing archive SHA entries before writing metadata.
    archive_root = ROOT / 'videos'
    expected_archive = manifest['archive_after']
    if len(expected_archive) != 266:
        raise RuntimeError('v19 archive inventory count changed')
    archive_before = {}
    for name, record in expected_archive.items():
        path = archive_root / name
        digest = sha(path)
        if digest != record['sha256']:
            raise RuntimeError('archive SHA mismatch: {}'.format(path))
        archive_before[str(path)] = digest

    manifest_path = ROOT / 'video_manifest_v20.json'
    index_path = ROOT / 'VIDEO_INDEX_v20.md'
    (OUT / 'README.md').write_text(
        '# Video collection v20 metadata correction\n\n'
        'v20은 v19 영상 모음을 바꾸지 않고 메타데이터만 교정한다. v19가 두 `strike_timed_entry_v1/native_retry_v1` 영상에 `continued_in_hold=false`를 기록했지만, 원본 report는 `phase_end=HOLD`, `stop_reason=source_terminal`이고 raw controls에는 79개 HOLD 제어행이 연속 기록되어 있다. 첫 HOLD 시각은 3.683333초이며 raw trace에도 41개 HOLD 표본이 기록되어 마지막 5.0초까지 이어진다. 이에 v20은 두 영상의 HOLD 여부를 true, 시각을 3.683333초로 고친다.\n\n'
        '기존 v19 index/manifest, report, controls, trace, collector와 이 producer의 SHA-256을 실행 전후 기록·대조했다. 기존 266개 archive 파일의 SHA도 inventory 값과 각각 비교했으며, 새 MP4 복사는 0개다. v19 원본은 변경하지 않는다.\n\n'
        '- [v19 index 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v19.md)\n'
        '- [v19 manifest 원본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_manifest_v19.json)\n'
        '- [v20 index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v20.md)\n'
        '- [v20 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_manifest_v20.json)\n'
        '- [수정 대상 native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/report.json), '
        '[controls](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/controls.json), '
        '[trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_timed_entry_v1/native_retry_v1/data/trace.json)\n'
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    index_path.write_text(index)

    after = {str(p): sha(p) for p in source_paths}
    if before != after:
        raise RuntimeError('a read-only input changed during correction')
    manifest['correction_audit']['source_sha256_before'] = before
    manifest['correction_audit']['source_sha256_after'] = after
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    archive_after = {path: sha(Path(path)) for path in archive_before}
    if archive_before != archive_after:
        raise RuntimeError('an archived video changed during correction')
    # The correction output must have no new copies and preserve all collection counts.
    out = load(manifest_path)
    if out['archive_count_after'] != 266 or out['new_unique_copies'] != 94 or out['new_video_copies_in_v20'] != 0:
        raise RuntimeError('v20 collection counts differ from v19 snapshot')
    print(json.dumps({
        'first_hold_time_s': first_hold_time,
        'hold_control_rows': len(hold_controls),
        'hold_trace_rows': len(hold_trace),
        'corrected_experiment_records': update_count,
        'corrected_index_rows': corrected,
        'archive_count_verified': len(archive_after),
        'new_video_copies': 0,
        'input_sha_unchanged': True,
        'collector_ast_verified': True,
    }, indent=2))


if __name__ == '__main__':
    main()
