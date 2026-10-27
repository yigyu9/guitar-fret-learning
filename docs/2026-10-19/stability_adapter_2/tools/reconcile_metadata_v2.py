#!/usr/bin/env python3
"""Create additive v2 documentation/metadata corrections; preserve all v1 outputs."""
from __future__ import annotations
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
N = ROOT / 'docs/2026-10-19/stability_adapter_2'
V12 = ROOT / 'docs/2026-10-12/video/om_no_strap_upper_arm_v1'
SOURCE = ROOT / 'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
FOCUS = ROOT / 'docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1'
PLAN = ROOT / 'stability_adapter_2/OCT19_GUITAR_POSTURE_ARCHIVE_PLAN_V1.md'
AGENTS = ROOT / 'stability_adapter_2/AGENTS.md'


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def snapshot(path: Path) -> dict:
    st = path.stat()
    return {'sha256': sha(path), 'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns}


def md_link(path: str, label: str) -> str:
    return f'[{label}]({path})'


def main() -> None:
    out_paths = [
        N/'video/manifest_v2.json', N/'video/INDEX_v2.md', N/'video/README_v2.md',
        N/'posture/README_v2.md', N/'guitar/README_v2.md',
        N/'images/guitar_focus_reference.png', N/'data/guitar/focus_source_README.md',
        N/'provenance_v2.json',
    ]
    if any(p.exists() for p in out_paths):
        raise FileExistsError('v2 destination already exists; preserve it and inspect manually')
    helper = Path(__file__).resolve()
    old_prov_path = N/'provenance_v1.json'
    old_prov_sha_before = sha(old_prov_path)
    old_prov = json.loads(old_prov_path.read_text(encoding='utf-8'))
    records = old_prov['copy_stage']['copy_records']
    rec_by_source = {x['source']: x for x in records}
    if len(rec_by_source) != len(records):
        raise RuntimeError('copy-stage source paths are not unique')

    old_outputs = old_prov['output_files_sha256_bytes']
    old_before = {}
    for item in old_outputs:
        p = Path(item['path'])
        if not p.is_file() or sha(p) != item['sha256'] or p.stat().st_size != item['bytes']:
            raise RuntimeError(f'old v1 output no longer matches its provenance: {p}')
        old_before[str(p)] = snapshot(p)
    old_before[str(old_prov_path)] = snapshot(old_prov_path)

    # Pin every original file represented by the original 61 exact-copy records,
    # the three source manifests, direct source docs/producers, and focus reference.
    source_pins = {Path(x['source']) for x in records}
    source_pins.update(V12/f'manifest_v{i}.json' for i in (1, 2, 3))
    source_pins.update({
        PLAN, AGENTS,
        ROOT/'stability_adapter_2/assets/om_body_geometry_v3/ATTRIBUTION.md',
        ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json',
        ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/README.md',
        ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/depth_v1.json',
        ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1/artifacts_v1/make_source_views_v1.py',
        SOURCE/'artifacts_candidate_v1/build_candidate_v1.py',
        SOURCE/'artifacts_candidate_v2/build_candidate_v2.py',
        SOURCE/'artifacts_candidate_v2/provenance_v2.json',
        SOURCE/'artifacts_candidate_v1/README.md',
        SOURCE/'artifacts_candidate_v2/README_v2.md',
        SOURCE/'README.md', SOURCE/'RESULT_SUMMARY_V2.md',
        SOURCE/'effort_verification_v10_cases4.json', SOURCE/'support_candidate_comparison_v1.json',
        SOURCE/'search_v9/upper_arm_neck_side/config.json',
        FOCUS/'README.md', FOCUS/'native_v1/media/initial_strings.png',
        ROOT/'docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/README.md',
    })
    source_before = {str(p): snapshot(p) for p in sorted(source_pins)}
    helper_before = snapshot(helper)

    # Verify the three original manifests against the source-hash declarations,
    # then resolve each video source to its independently recorded copy target.
    merged = []
    used_sources = set()
    for version in (1, 2, 3):
        manifest_path = V12/f'manifest_v{version}.json'
        source_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        for item in source_manifest['videos']:
            src = item['source']
            if src in used_sources:
                raise RuntimeError(f'duplicate source in source manifests: {src}')
            used_sources.add(src)
            rec = rec_by_source.get(src)
            if rec is None:
                raise RuntimeError(f'video has no exact-copy record: {src}')
            source_path = Path(src)
            actual_copy = Path(rec['destination'])
            source_sha = sha(source_path)
            copy_sha = sha(actual_copy)
            if source_sha != item['source_sha256'] or source_sha != rec['sha256_before'] or source_sha != rec['sha256_after']:
                raise RuntimeError(f'source SHA mismatch for {src}')
            if copy_sha != rec['copy_sha256'] or copy_sha != source_sha:
                raise RuntimeError(f'copy SHA mismatch for {actual_copy}')
            if item['copy_sha256'] != source_sha:
                raise RuntimeError(f'old video manifest source/copy SHA mismatch for {src}')
            merged.append({
                'source': src, 'source_sha256': source_sha,
                'destination': str(actual_copy), 'copy_sha256': copy_sha,
                'label': item['label'], 'view': item['view'],
                'source_manifest': str(manifest_path),
            })
    if len(merged) != 22 or len(used_sources) != 22:
        raise RuntimeError(f'expected 22 completed videos, found {len(merged)}')
    if len({x['destination'] for x in merged}) != 22:
        raise RuntimeError('video destination paths are not unique')
    if len({x['source'] for x in merged}) != 22:
        raise RuntimeError('video source paths are not unique')
    manifest_v2 = {'schema_version': 2,
                   'description': 'v2 repairs source-to-copy destination mappings from the exact-copy records; no MP4 was copied or changed.',
                   'videos': merged}
    (N/'video/manifest_v2.json').write_text(json.dumps(manifest_v2, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

    groups = []
    for item in merged:
        src = item['source']
        if '/native_v11/' in src:
            section = 'Native 11 · upper_arm_neck_side'
        elif '/native_v12/' in src:
            section = 'Native 12 · upper_arm_neck_side_repeat'
        else:
            trial = src.split('/native_v',1)[1].split('/',1)[0]
            section = f'시험 {int(trial):02d} · {item["label"].split("·",1)[-1].strip() if "·" in item["label"] else item["label"].split(":",1)[-1].strip()}'
        groups.append((section, item))
    index_lines = [
        '# 영상 INDEX · v2', '',
        '이 v2 색인은 기존 manifest v1의 목적지 연결 오류만 보완합니다. v1의 22개 source→destination 행 중 진단 영상 18개가 네 candidate 목적지에 잘못 연결되어 있었습니다. 아래는 원본 manifest 세 개의 label/view/source SHA와 provenance v1의 정확 복사 기록에서 목적지를 다시 대조한 결과입니다. 영상 bytes 재복사·재인코딩은 0회입니다.', '',
        '모든 링크는 2026-10-19 보관 사본의 절대경로입니다. manifest에는 22개의 고유 source와 22개의 고유 destination이 있으며 각 원본·사본 SHA-256이 같습니다.', '',
        '## 동일 초기조건 후보', '',
    ]
    last = None
    for section, item in groups:
        if '/native_v11/' not in item['source'] and '/native_v12/' not in item['source']:
            continue
        if section != last:
            index_lines += [f'### {section}', '']
            last = section
        index_lines += [f'- {item["view"]}: {md_link(item["destination"], item["label"] + " · " + item["view"])}']
    index_lines += ['', '## 과거 진단 시험', '']
    last = None
    for section, item in groups:
        if '/native_v11/' in item['source'] or '/native_v12/' in item['source']:
            continue
        if section != last:
            if last is not None:
                index_lines.append('')
            index_lines += [f'### {section}', '']
            last = section
        index_lines += [f'- {item["view"]}: {md_link(item["destination"], item["label"] + " · " + item["view"])}']
    index_lines += ['', 'Native 8의 1-frame/0.034초 조각은 완료 trial 목록에서 제외했고 별도 원본 링크로만 설명합니다. 시험별 해석과 제한은 [자세 문서 v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/posture/README_v2.md)에서 확인합니다.', '']
    (N/'video/INDEX_v2.md').write_text('\n'.join(index_lines), encoding='utf-8')

    video_readme = '''# 자세 실험 영상 보관 · v2\n\n이 v2는 이미 복사된 영상을 다시 쓰지 않고, manifest v1에서 발견된 source→destination 대응 오류만 수정합니다. v1에는 22행이 있었지만 목적지는 4개뿐이어서 과거 진단 영상 18개가 native 12 후보 파일로 잘못 연결되어 있었습니다. v2는 세 원본 manifest의 source SHA·label·view와 provenance v1의 61개 복사 기록에서 각 실제 destination을 다시 결합했습니다. 새 manifest에는 22개 고유 source와 22개 고유 destination이 있으며 source SHA, copy SHA 및 실제 파일이 모두 일치합니다.\n\n완료 영상은 후보 native 11/12 전신·손 4개와 이전 완료 진단 시험 1–7·9–10 전신·손 18개입니다. 후보는 동일 초기조건의 5초 유지 자료일 뿐, 움직이는 연주 강건성이나 학습 성공이 아닙니다. 과거 시험의 해석은 [v2 영상 INDEX](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/INDEX_v2.md)와 [자세 설명 v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/posture/README_v2.md)에 정리했습니다.\n\n미완료 native 8은 첫 step assertion 실패로 physics 0, 1 frame/약0.034초입니다. 완료 영상 22개에 넣지 않았습니다. [원본 whole_body](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/whole_body.mp4), [원본 hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/hands.mp4).\n\n[정정 manifest v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/manifest_v2.json) · [v2 입력·보존·출력 SHA 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/provenance_v2.json). v1 files, MP4 bytes와 source 실험 자료는 변경하지 않았습니다.\n'''
    (N/'video/README_v2.md').write_text(video_readme, encoding='utf-8')

    # Clarify the rate/domain of the 1200 physics endpoint counts versus the
    # separate RH-finger 60 Hz query; leave README v1 unchanged.
    posture = (N/'posture/README.md').read_text(encoding='utf-8')
    old = '보고된 접촉 표본은 60 Hz 단위이며 연속 240 Hz 무접촉 인증으로 확대하지 않습니다.'
    new = '표의 1200개 접촉 표본은 240 Hz physics endpoint k=1…1200에서 센 값입니다. 별도의 RHfinger 접촉 query는 60 Hz에서 299개 표본(k=4…1196)만 확인했습니다. 이 60 Hz RHfinger query를 다른 240 Hz step까지의 전기간 무접촉 인증으로 확대하지 않습니다.'
    if old not in posture:
        raise RuntimeError('expected v1 posture frequency sentence not found')
    posture = posture.replace(old, new)
    posture = posture.replace('# 스트랩 없는 초기 자세 후보', '# 스트랩 없는 초기 자세 후보 · v2\n\n이 v2는 접촉 표본의 주파수 설명을 분리합니다. 이전 문서 v1의 한 문장은 모든 표본을 60 Hz로 읽을 여지가 있어, 표의 1200 physics endpoint와 RHfinger 전용 299-query 한계를 명시합니다. 기존 v1 문서는 보존했습니다.\n')
    posture += '\n\n영상 destination 대조 오류 보완은 [영상 INDEX v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/INDEX_v2.md)와 [manifest v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/manifest_v2.json)를 참조합니다.\n'
    (N/'posture/README_v2.md').write_text(posture, encoding='utf-8')

    # Exact-copy the previous guitar-focused native image and its source README.
    focus_image_src = FOCUS/'native_v1/media/initial_strings.png'
    focus_readme_src = FOCUS/'README.md'
    focus_image_dst = N/'images/guitar_focus_reference.png'
    focus_readme_dst = N/'data/guitar/focus_source_README.md'
    shutil.copyfile(focus_image_src, focus_image_dst)
    shutil.copyfile(focus_readme_src, focus_readme_dst)
    if sha(focus_image_src) != sha(focus_image_dst) or sha(focus_readme_src) != sha(focus_readme_dst):
        raise RuntimeError('focus reference exact-copy mismatch')

    guitar = (N/'guitar/README.md').read_text(encoding='utf-8')
    insert = '''## 과거 기타 초점 화면 참고\n\n아래는 실제 Isaac Gym의 기타 중심 카메라에서 얻은 이미지이며 물리 없는 6현 표시를 포함합니다. 이 이미지는 `guitar_focused_view_v1`의 과거 다른 초기 자세 모델 보기입니다. 현재 native 11/12 후보의 초기 화면이 아니며 현재 자세의 근거로 사용하지 않습니다.\n\n![과거 다른 초기 자세의 기타 중심 Isaac Gym 화면; 현재 후보 장면이 아님](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/guitar_focus_reference.png)\n\n- [원본 설명 복사본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/guitar/focus_source_README.md)\n- [원래 source 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/native_v1/media/initial_strings.png)\n\n'''
    guitar = guitar.replace('# 기타 형상과 표시 범위', '# 기타 형상과 표시 범위 · v2\n\n이 v2는 기존 형상 설명을 유지하고, 요청된 과거 기타 중심 native 이미지를 추가하며 현재 후보와 구분합니다. v1 문서는 보존했습니다.\n')
    guitar = guitar.replace('## 질량과 출처 범위', insert+'## 질량과 출처 범위')
    (N/'guitar/README_v2.md').write_text(guitar, encoding='utf-8')

    # Recheck every pinned source and old v1 output after new writes.
    source_after = {str(p): snapshot(p) for p in sorted(source_pins)}
    old_after = {path: snapshot(Path(path)) for path in old_before}
    helper_after = snapshot(helper)
    if source_before != source_after:
        raise RuntimeError('one or more source inputs changed while v2 files were created')
    if any(old_before[k] != old_after[k] or old_outputs_by_path.get(k, {}).get('sha256') not in (None, old_after[k]['sha256']) for k in old_before):
        raise RuntimeError('an existing v1 archive output changed during v2 reconciliation')
    if helper_before != helper_after:
        raise RuntimeError('reconciliation helper changed during run')
    if sha(old_prov_path) != old_prov_sha_before:
        raise RuntimeError('provenance v1 changed')

    new_files = [N/'video/manifest_v2.json', N/'video/INDEX_v2.md', N/'video/README_v2.md',
                 N/'posture/README_v2.md', N/'guitar/README_v2.md', N/'images/guitar_focus_reference.png',
                 N/'data/guitar/focus_source_README.md', helper]
    outputs = [{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in new_files]
    v1_snapshot_records = [{'path':k,'sha256_before':v['sha256'],'sha256_after':old_after[k]['sha256'],
                            'bytes_before':v['bytes'],'bytes_after':old_after[k]['bytes'],
                            'unchanged':v==old_after[k]} for k,v in old_before.items()]
    new_prov = {
        'schema_version':2,
        'purpose':'기존 v1 보존 상태에서 영상 source→destination 메타데이터 오류, 접촉 주파수 문구, 기타 초점 참고 이미지를 보완',
        'no_new_physics_training_or_video_copy':True,
        'video_mapping_validation':{'source_manifest_files':[str(V12/f'manifest_v{i}.json') for i in (1,2,3)],
            'video_rows':len(merged),'unique_sources':len(used_sources),'unique_destinations':len({x['destination'] for x in merged}),
            'source_sha_equals_declared_and_copy_sha':True,'actual_destination_sha_verified':True,
            'mp4_recopy_count':0,'reencoding_count':0},
        'v1_preservation':{'old_output_count':len(old_before),'old_outputs_unchanged':all(x['unchanged'] for x in v1_snapshot_records),
                           'records':v1_snapshot_records,'provenance_v1_sha256_before':old_prov_sha_before,
                           'provenance_v1_sha256_after':sha(old_prov_path)},
        'direct_inputs_before':source_before,'direct_inputs_after':source_after,
        'reconciliation_helper_sha256_before':helper_before['sha256'],'reconciliation_helper_sha256_after':helper_after['sha256'],
        'focus_reference_copy':{'source':str(focus_image_src),'source_sha256_before':sha(focus_image_src),
            'source_sha256_after':sha(focus_image_src),'destination':str(focus_image_dst),'copy_sha256':sha(focus_image_dst),
            'source_readme':str(focus_readme_src),'source_readme_sha256':sha(focus_readme_src),
            'readme_copy':str(focus_readme_dst),'readme_copy_sha256':sha(focus_readme_dst)},
        'new_outputs_sha256_bytes':outputs,
        'self_hash_note':'이 파일은 자기 해시를 포함하지 않으며 root 독립 검증에서 해시할 것.'
    }
    (N/'provenance_v2.json').write_text(json.dumps(new_prov,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'videos':len(merged),'unique_destinations':len({x['destination'] for x in merged}),
        'v1_files_preserved':all(x['unchanged'] for x in v1_snapshot_records),'focus_copy_sha':sha(focus_image_dst),
        'new_outputs':len(outputs),'provenance_v2_sha256':sha(N/'provenance_v2.json')},ensure_ascii=False))

# Populate this mapping after initial v1 provenance read; used only as a guard.
old_outputs_by_path: dict[str, dict] = {}

if __name__ == '__main__':
    # Load expected hashes before starting the write phase.
    _prov=json.loads((N/'provenance_v1.json').read_text(encoding='utf-8'))
    old_outputs_by_path={x['path']:x for x in _prov['output_files_sha256_bytes']}
    main()
