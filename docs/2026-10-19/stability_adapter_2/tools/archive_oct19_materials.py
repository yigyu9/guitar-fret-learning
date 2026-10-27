#!/usr/bin/env python3
"""Byte-exact archive copier for the 2026-10-19 documentation package."""
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
DEST = ROOT / 'docs/2026-10-19/stability_adapter_2'
VIDEO_ROOT = ROOT / 'docs/2026-10-12/video/om_no_strap_upper_arm_v1'
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
OM = RESULTS / 'om_no_strap_upper_arm_v1'
GEOM = ROOT / 'stability_adapter_2/assets/om_body_geometry_v3'
GEOM_OLD = RESULTS / 'om_body_geometry_v1'


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def add(src: Path, rel: str, group: str = 'copied_input') -> None:
    COPY_MAP.append((src, DEST / rel, group))

COPY_MAP: list[tuple[Path, Path, str]] = []
# Geometry, source documentation, and already-reviewed figures.
add(GEOM / 'manifest.json', 'data/guitar/geometry_v3_manifest.json')
add(GEOM / 'ATTRIBUTION.md', 'data/guitar/ATTRIBUTION_source.md')
add(GEOM_OLD / 'depth_v1.json', 'data/guitar/depth_v1.json')
add(GEOM_OLD / 'README.md', 'data/guitar/geometry_source_README.md')
add(GEOM_OLD / 'artifacts_v1/source_mesh_three_views.png', 'images/source_mesh_three_views.png')
add(GEOM_OLD / 'artifacts_v1/local_depth_samples.png', 'images/local_depth_samples.png')
# Current candidate visuals from consumed, immutable source outputs.
ART2 = OM / 'artifacts_candidate_v2'
add(ART2 / 'native11_initial_and_timeline_v2.png', 'images/native11_initial_and_timeline_v2.png')
add(ART2 / 'native11_zero_to_five_comparison_v2.png', 'images/native11_zero_to_five_comparison_v2.png')
# Current native11/12 capture reference images (not rendered anew).
for run, key in [('native_v11/upper_arm_neck_side', 'native11'),
                 ('native_v12/upper_arm_neck_side_repeat', 'native12')]:
    base = OM / run / 'media'
    add(base / 'initial_strings.png', f'images/{key}_initial_strings.png')
    add(base / 'initial_support_side.png', f'images/{key}_initial_support_side.png')
    for frame in ('00000', '00060', '00150'):
        add(base / f'frames/whole_body/{frame}.png', f'images/{key}_whole_body_{frame}.png')
# Compact data package preserving source files exactly.
for source, dest in [
    (OM / 'effort_verification_v10_cases4.json', 'data/posture/effort_verification_v10_cases4.json'),
    (OM / 'support_candidate_comparison_v1.json', 'data/posture/support_candidate_comparison_v1.json'),
    (OM / 'RESULT_SUMMARY_V2.md', 'data/posture/RESULT_SUMMARY_V2_source.md'),
    (OM / 'README.md', 'data/posture/README_source.md'),
    (OM / 'search_v9/upper_arm_neck_side/config.json', 'data/posture/search_v9_upper_arm_neck_side_config.json'),
    (OM / 'search_v9/upper_arm_neck_side/candidate.json', 'data/posture/search_v9_upper_arm_neck_side_candidate.json'),
]: add(source, dest)
for run, key in [('native_v11/upper_arm_neck_side', 'native11'),
                 ('native_v12/upper_arm_neck_side_repeat', 'native12')]:
    base = OM / run
    for name, destname in [('attempt.json', 'attempt.json'), ('report.json', 'report.json'),
                           ('initial_values.json', 'initial_values.json'),
                           ('native_properties.json', 'native_properties.json'),
                           ('media/effort_configuration.json', 'effort_configuration.json'),
                           ('media/capture.json', 'capture.json')]:
        add(base / name, f'data/posture/{key}_{destname}')
# Preserve the original video manifests for traceability.
for v in (1, 2, 3):
    add(VIDEO_ROOT / f'manifest_v{v}.json', f'data/video_source_manifests/manifest_v{v}.json')

# The source video manifests contain all 22 completed MP4s. Keep each source,
# and only change the new archive destination.
VIDEO_ENTRIES = []
for v in (1, 2, 3):
    manifest_path = VIDEO_ROOT / f'manifest_v{v}.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for item in manifest['videos']:
        src = Path(item['source'])
        if v == 3:
            bucket = 'candidate'
            new_name = ('native11_' if 'native_v11/' in str(src) else 'native12_') + item['view'] + '.mp4'
        else:
            bucket = 'diagnostics'
            # Preserve the original archive basename to avoid accidental merging.
            new_name = Path(item['destination']).name
        dst = DEST / 'video' / bucket / new_name
        COPY_MAP.append((src, dst, f'video_manifest_v{v}'))
        VIDEO_ENTRIES.append({
            'source': str(src),
            'source_sha256_declared': item['source_sha256'],
            'source_sha256_before': None,
            'source_sha256_after': None,
            'destination': str(dst),
            'copy_sha256': None,
            'bytes': None,
            'label': item['label'],
            'view': item['view'],
            'source_manifest': str(manifest_path),
        })

# Pin directly consulted documents, source producers/helpers, and font even
# though this package reuses already-rendered images and does not render anew.
PIN_INPUTS = [
    ROOT / 'stability_adapter_2/AGENTS.md',
    ROOT / 'stability_adapter_2/OCT19_GUITAR_POSTURE_ARCHIVE_PLAN_V1.md',
    GEOM / 'ATTRIBUTION.md', GEOM / 'manifest.json',
    GEOM_OLD / 'README.md', GEOM_OLD / 'depth_v1.json',
    GEOM_OLD / 'artifacts_v1/source_mesh_three_views.png',
    GEOM_OLD / 'artifacts_v1/local_depth_samples.png',
    GEOM_OLD / 'artifacts_v1/make_source_views_v1.py',
    OM / 'README.md', OM / 'RESULT_SUMMARY_V2.md',
    OM / 'effort_verification_v10_cases4.json', OM / 'support_candidate_comparison_v1.json',
    OM / 'search_v9/upper_arm_neck_side/config.json',
    OM / 'artifacts_candidate_v1/build_candidate_v1.py',
    OM / 'artifacts_candidate_v2/build_candidate_v2.py',
    OM / 'artifacts_candidate_v2/provenance_v2.json',
    OM / 'artifacts_candidate_v2/native11_initial_and_timeline_v2.png',
    OM / 'artifacts_candidate_v2/native11_zero_to_five_comparison_v2.png',
    Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf'),
] + [VIDEO_ROOT / f'manifest_v{v}.json' for v in (1, 2, 3)]
for run in ('native_v11/upper_arm_neck_side', 'native_v12/upper_arm_neck_side_repeat'):
    base = OM / run
    PIN_INPUTS += [base / x for x in ('attempt.json','report.json','initial_values.json','native_properties.json',
                                      'media/effort_configuration.json','media/capture.json','media/initial_strings.png',
                                      'media/initial_support_side.png','media/frames/whole_body/00000.png',
                                      'media/frames/whole_body/00060.png','media/frames/whole_body/00150.png')]


def main() -> None:
    pre = {str(p): {'sha256': sha256(p), 'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns}
           for p in PIN_INPUTS}
    seen = set()
    copied = []
    for src, dst, group in COPY_MAP:
        if str(dst) in seen:
            raise RuntimeError(f'duplicate destination: {dst}')
        seen.add(str(dst))
        if not src.is_file():
            raise FileNotFoundError(src)
        src_stat = src.stat()
        before = sha256(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        after = sha256(src)
        out = sha256(dst)
        if before != after or before != out or src_stat.st_size != src.stat().st_size or src_stat.st_mtime_ns != src.stat().st_mtime_ns:
            raise RuntimeError(f'source changed or copy mismatch: {src}')
        copied.append({'source': str(src), 'destination': str(dst), 'sha256_before': before,
                       'sha256_after': after, 'copy_sha256': out, 'bytes': dst.stat().st_size,
                       'source_bytes': src.stat().st_size, 'source_mtime_ns_before': src_stat.st_mtime_ns,
                       'source_mtime_ns_after': src.stat().st_mtime_ns, 'group': group})
    post = {str(p): {'sha256': sha256(p), 'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns}
            for p in PIN_INPUTS}
    if pre != post:
        raise RuntimeError('one or more pinned inputs changed during archive copy')
    # Make video manifest reflect the new archive paths and verified hashes.
    by_dst = {x['destination']: x for x in copied}
    for item in VIDEO_ENTRIES:
        rec = by_dst[item['destination']]
        item.update(source_sha256_before=rec['sha256_before'], source_sha256_after=rec['sha256_after'],
                    copy_sha256=rec['copy_sha256'], bytes=rec['bytes'])
        if item['source_sha256_declared'] != rec['sha256_before']:
            raise RuntimeError(f"source manifest SHA mismatch: {item['source']}")
    archive_manifest = {'schema_version': 1, 'description': '2026-10-19 exact-copy video archive; no re-encoding',
                        'videos': VIDEO_ENTRIES}
    (DEST / 'video/manifest_v1.json').write_text(json.dumps(archive_manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = {'schema_version': 1, 'archive_copy_run': 'archive_oct19_materials.py',
              'copy_count': len(copied), 'video_count': len(VIDEO_ENTRIES), 'copy_records': copied,
              'pin_inputs_before': pre, 'pin_inputs_after': post,
              'source_change_count': sum(1 for a,b in zip(pre.values(),post.values()) if a != b),
              'new_physics_or_training_runs': 0}
    (DEST / 'tools/provenance_copy_stage.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'copy_count': len(copied), 'video_count': len(VIDEO_ENTRIES),
                      'bytes': sum(x['bytes'] for x in copied),
                      'source_change_count': report['source_change_count']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
