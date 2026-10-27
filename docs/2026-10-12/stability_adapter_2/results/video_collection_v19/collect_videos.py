#!/usr/bin/env python3
"""Snapshot and copy completed result videos into the v19 archive, without re-encoding."""
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
DOCS = ROOT / 'docs/2026-10-12/stability_adapter_2'
RESULTS = DOCS / 'results'
ARCHIVE = DOCS / 'videos'
INDEX = DOCS / 'VIDEO_INDEX_v19.md'
MANIFEST = DOCS / 'video_manifest_v19.json'
OUT_DIR = RESULTS / 'video_collection_v19'
SNAPSHOT = '2026-10-10T07:22:14+09:00'
OLD_COUNT = 172
PRESERVED_PARTS = ('source_before', 'source_final', 'source_snapshot', 'collection_source', 'analysis_source')


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def preserved_copy(rel):
    return any(part.startswith(PRESERVED_PARTS) for part in rel.parts)


def run_json(argv, timeout=120):
    p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def probe(path):
    cmd = ['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
           '-show_entries', 'stream=codec_name,width,height,avg_frame_rate,nb_read_frames,duration',
           '-show_entries', 'format=duration', '-of', 'json', str(path)]
    rc, out, err = run_json(cmd, timeout=60)
    if rc:
        return {'ok': False, 'error': (err or out).strip()[-1000:]}
    data = json.loads(out)
    streams = data.get('streams', [])
    if not streams:
        return {'ok': False, 'error': 'ffprobe found no video stream'}
    stream = streams[0]
    duration = stream.get('duration') or data.get('format', {}).get('duration')
    frames = stream.get('nb_read_frames')
    return {'ok': bool(duration and frames and int(frames) > 0),
            'codec': stream.get('codec_name'), 'width': stream.get('width'),
            'height': stream.get('height'), 'fps': stream.get('avg_frame_rate'),
            'frames': int(frames) if frames and frames.isdigit() else None,
            'duration_s': float(duration) if duration else None,
            'error': None if duration and frames else 'missing duration/frame count'}


def decode(path):
    rc, out, err = run_json(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'null', '-'], timeout=120)
    return {'ok': rc == 0, 'returncode': rc, 'error': (err or out).strip()[-1000:] or None}


def best_nearby_json(phase_root, source, name):
    candidates = []
    for p in phase_root.rglob(name):
        rel = p.relative_to(phase_root)
        if preserved_copy(rel):
            continue
        try:
            common = len(os.path.commonpath([str(p.parent), str(source.parent)]).split(os.sep))
        except ValueError:
            common = 0
        candidates.append((common, -len(p.parts), str(p), p))
    return max(candidates)[-1] if candidates else None


def phase_metadata(source):
    rel = source.relative_to(RESULTS)
    phase_root = RESULTS / rel.parts[0]
    readme = phase_root / 'README.md'
    if not readme.exists():
        readme = next(iter(sorted(phase_root.glob('*.md'))), None)
    report_path = best_nearby_json(phase_root, source, 'report.json')
    initial_path = best_nearby_json(phase_root, source, 'initial_values.json')
    report = {}
    if report_path:
        try:
            report = json.loads(report_path.read_text())
        except Exception:
            report = {}
    analysis_path = best_nearby_json(phase_root, source, 'summary.json')
    summary = {}
    if analysis_path:
        try:
            summary = json.loads(analysis_path.read_text())
            if isinstance(summary.get('trials'), list) and summary['trials']:
                summary = summary['trials'][0]
        except Exception:
            summary = {}
    completed_run = report.get('completed_5s')
    if completed_run is None:
        completed_run = summary.get('completed_5s')
    if completed_run is None:
        completed_run = None
    failure = report.get('failure') or summary.get('failure')
    terminal_time = report.get('source_terminal_time_s', summary.get('source_terminal_time_s'))
    phase_end = report.get('phase_end', summary.get('phase_end'))
    return {
        'phase': rel.parts[0],
        'source_readme': str(readme) if readme and readme.exists() else None,
        'initial_values': str(initial_path) if initial_path else None,
        'report': str(report_path) if report_path else None,
        'completed_5s': completed_run,
        'failure': failure,
        'phase_end': phase_end,
        'stop_reason': report.get('stop_reason', summary.get('stop_reason')),
        'terminal_time_s': terminal_time,
        'continued_in_hold': bool(phase_end == 'HOLD' and terminal_time is not None and completed_run is True),
    }


def archive_name(source):
    rel = source.relative_to(RESULTS)
    parts = list(rel.parts[:-1])
    parts = [p for p in parts if p not in ('data', 'images')]
    stem = source.stem
    return '__'.join(parts + [stem]) + '.mp4'


def mdlink(path, label):
    return '[{}]({})'.format(label, path) if path else '—'


def main():
    snapshot_dt = datetime.fromisoformat(SNAPSHOT)
    snapshot_ts = snapshot_dt.timestamp()
    existing_files = sorted(p for p in ARCHIVE.iterdir() if p.is_file())
    if len(existing_files) != OLD_COUNT:
        raise RuntimeError('Expected {} v18 videos, found {}; archive left untouched'.format(OLD_COUNT, len(existing_files)))
    old_state = {p.name: {'sha256': sha256(p), 'size': p.stat().st_size} for p in existing_files}
    existing_sha = {}
    for name, row in old_state.items():
        existing_sha.setdefault(row['sha256'], []).append(name)

    excluded = []
    newer = []
    by_sha = {}
    for source in sorted(RESULTS.rglob('*.mp4')):
        rel = source.relative_to(RESULTS)
        if rel.parts[0] == OUT_DIR.name or preserved_copy(rel):
            excluded.append({'source': str(source), 'reason': 'preserved source copy/output directory'})
            continue
        stat = source.stat()
        if stat.st_mtime > snapshot_ts:
            newer.append({'source': str(source), 'reason': 'modified after snapshot; possible active output'})
            continue
        digest_before = sha256(source)
        meta = phase_metadata(source)
        probe_info = probe(source)
        decode_info = decode(source) if probe_info.get('ok') else {'ok': False, 'returncode': None, 'error': 'ffprobe failed'}
        path_partial = any('partial' in part.lower() for part in rel.parts)
        complete = bool(probe_info.get('ok') and decode_info.get('ok') and not path_partial
                        and not meta.get('failure') and meta.get('completed_5s') is not False)
        if not complete:
            status = 'partial_or_incomplete'
        else:
            status = 'pending'
        row = {
            'source': str(source), 'relative_source': str(rel), 'sha256_source_before': digest_before,
            'size_bytes': stat.st_size, 'probe': probe_info, 'full_decode': decode_info,
            'experiment': meta, 'complete_video': complete, 'status': status,
            'archive_copy': None, 'sha256_copy': None, 'sha256_source_after': None,
        }
        by_sha.setdefault(digest_before, []).append(row)

    new_copies = []
    for digest, rows in sorted(by_sha.items(), key=lambda item: min(r['relative_source'] for r in item[1])):
        complete_rows = [r for r in rows if r['complete_video']]
        if not complete_rows:
            continue
        if digest in existing_sha:
            archive_file = existing_sha[digest][0]
            for row in complete_rows:
                row['status'] = 'already_in_v18'
                row['archive_copy'] = str(ARCHIVE / archive_file)
                row['sha256_copy'] = digest
                row['sha256_source_after'] = sha256(row['source'])
            continue
        representative = complete_rows[0]
        source = Path(representative['source'])
        name = archive_name(source)
        target = ARCHIVE / name
        if target.exists() and sha256(target) != digest:
            target = target.with_name(target.stem + '__' + digest[:8] + target.suffix)
        counter = 2
        while target.exists() and sha256(target) != digest:
            target = target.with_name(target.stem + '_' + str(counter) + target.suffix)
            counter += 1
        source_before = sha256(source)
        if not target.exists():
            shutil.copyfile(source, target)
        copy_sha = sha256(target)
        source_after = sha256(source)
        if not (source_before == copy_sha == source_after == digest):
            raise RuntimeError('SHA mismatch while copying {}'.format(source))
        entry = {'source': str(source), 'copy': str(target), 'sha256_before': source_before,
                 'sha256_copy': copy_sha, 'sha256_after': source_after,
                 'ffprobe': representative['probe'], 'experiment': representative['experiment']}
        new_copies.append(entry)
        for row in complete_rows:
            row['status'] = 'copied' if row is representative else 'same_sha_alias'
            row['archive_copy'] = str(target)
            row['sha256_copy'] = copy_sha
            row['sha256_source_after'] = sha256(row['source'])

    after_files = sorted(p for p in ARCHIVE.iterdir() if p.is_file())
    after_state = {p.name: {'sha256': sha256(p), 'size': p.stat().st_size} for p in after_files}
    for name, row in old_state.items():
        if after_state.get(name) != row:
            raise RuntimeError('Existing v18 archive file changed: {}'.format(name))

    # Catch output files created after the initial directory walk while this collection ran.
    known_newer = {row['source'] for row in newer}
    for path in RESULTS.rglob('*.mp4'):
        rel = path.relative_to(RESULTS)
        if rel.parts[0] == OUT_DIR.name or preserved_copy(rel):
            continue
        if path.stat().st_mtime > snapshot_ts and str(path) not in known_newer:
            newer.append({'source': str(path), 'reason': 'modified after snapshot; possible active output'})
            known_newer.add(str(path))

    entries = [row for rows in by_sha.values() for row in rows]
    entries.sort(key=lambda r: r['relative_source'])
    manifest = {
        'version': 19, 'snapshot_captured_at': SNAPSHOT,
        'existing_v18_count_before': len(old_state), 'existing_v18_unchanged': True,
        'archive_count_after': len(after_state), 'new_unique_copies': len(new_copies),
        'result_mp4_sources_scanned': len(entries), 'preserved_source_copies_excluded': excluded,
        'newer_than_snapshot_excluded': newer,
        'new_copies': new_copies, 'source_inventory': entries,
        'archive_before': old_state, 'archive_after': after_state,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')

    best_phase = 'strike_terminal_retract_v1'
    best_names = {}
    for entry in new_copies:
        if best_phase in entry['source']:
            stem = Path(entry['source']).stem
            best_names[stem] = Path(entry['copy']).name
    lines = [
        '# Native video collection v19 — {}개'.format(len(after_state)), '',
        '스냅샷 시각: {} (Asia/Seoul). v18 영상 172개는 모두 SHA-256을 전후 대조해 그대로 유지했다. 이 스냅샷에서 D/results의 MP4 {}개 경로를 검사했고, source 보존 사본과 스냅샷 시각 이후 변경된 파일은 신규 영상으로 세지 않았다. 완료된 새 고유 영상 {}개를 re-encode 없이 복사해 v19 모음은 {}개다. 전체 원본 검사 상태·SHA·ffprobe·복사 전후 확인은 [manifest]({})에 있다.'.format(
            SNAPSHOT, len(entries), len(new_copies), len(after_state), str(MANIFEST)), '',
        '## 현재 가장 나은 부분 결과: terminal-retract', '',
        '연주 prefix에는 네 번의 적시 타현이 있지만 source wrong-crossing terminal로 종료되어 완성 연주는 아니다. 이 영상은 terminal 이후 HOLD에서 오른팔을 회수한 가장 나은 현재 부분 결과를 보여준다. 회수 구간 개선을 음악 성공으로 해석하지 않는다.', '',
    ]
    for camera in ('whole_body', 'hands'):
        copied = best_names.get(camera)
        if copied:
            lines.append('![Terminal-retract {} native video]({})'.format(camera, str(ARCHIVE / copied)))
            lines.append('')
    lines += ['[실험 결과와 HOLD 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/README.md:1) · [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_terminal_retract_v1/native/data/initial_values.json) · source phase가 3.633333초에 terminal 된 뒤 HOLD에서 physics가 5초까지 계속됐다.', '',
              '## 새로 추가되거나 SHA로 매핑된 완료 영상', '',
              '각 행은 source MP4와 archive copy를 SHA로 연결한다. 같은 source SHA는 한 번만 복사하고 나머지는 같은 copy에 alias로 매핑했다. Source README/initial values와 source terminal 뒤 HOLD 여부는 각 행에 표시한다.', '',
              '| Source phase / camera | 원본 MP4 | v19 모음 파일 | SHA-256 | 재생시간 / fps | terminal 후 HOLD | 실험 README | 초기값 |',
              '|---|---|---|---|---|---|---|---|']
    for digest, rows in sorted(by_sha.items(), key=lambda item: min(r['relative_source'] for r in item[1])):
        complete_rows = [r for r in rows if r['complete_video']]
        if not complete_rows:
            continue
        first = complete_rows[0]
        if first['status'] == 'already_in_v18':
            continue
        aliases = complete_rows
        for row in aliases:
            pinfo = row['probe']; emeta = row['experiment']
            camera = Path(row['source']).stem
            lines.append('| {} / {} | {} | {} | `{}` | {}초 / {} | {} | {} | {} |'.format(
                emeta.get('phase','—'), camera,
                mdlink(row['source'], row['relative_source']),
                mdlink(row['archive_copy'], Path(row['archive_copy']).name),
                digest,
                '{:.6f}'.format(pinfo['duration_s']) if pinfo.get('duration_s') is not None else '—', pinfo.get('fps','—'),
                '예' if emeta.get('continued_in_hold') else ('아니오' if emeta.get('phase_end') else '기록 없음'),
                mdlink(emeta.get('source_readme'), 'README') if emeta.get('source_readme') else '없음',
                mdlink(emeta.get('initial_values'), 'initial_values.json') if emeta.get('initial_values') else '없음'))
    invalid = [r for r in entries if not r['complete_video']]
    if invalid:
        lines += ['', '## partial 또는 완료 확인 실패', '', '원본은 보존했으며 모음에 복사하지 않았다. 검사 오류와 source path는 manifest의 `source_inventory`에서 확인할 수 있다.', '']
        for row in invalid:
            lines.append('- `{}` — {}; ffprobe={}, full decode={}, run completed_5s={}, failure={}'.format(
                row['relative_source'], row['status'], row['probe'].get('error'), row['full_decode'].get('error'),
                row['experiment'].get('completed_5s'), row['experiment'].get('failure')))
    lines += ['', '기존 [v18 인덱스 172개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v18.md:1)는 수정 없이 유지한다. [v19 수집기와 방법](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/video_collection_v19/README.md:1).', '']
    tmp = INDEX.with_suffix('.md.tmp')
    tmp.write_text('\n'.join(lines))
    tmp.replace(INDEX)
    print(json.dumps({'snapshot': SNAPSHOT, 'scanned': len(entries), 'new_copies': len(new_copies),
                      'excluded_preserved': len(excluded), 'excluded_newer': len(newer),
                      'invalid_or_partial': len(invalid), 'archive_after': len(after_state)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
