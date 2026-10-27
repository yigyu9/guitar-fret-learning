"""Copy this experiment's existing videos into one folder; leave originals intact."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs/2026-10-12/stability_adapter_2'
RESULTS = DOCS / 'results'
SUFFIXES = {'.mp4', '.webm', '.avi', '.mov', '.mkv', '.gif'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = DOCS / 'videos'
    index = DOCS / 'VIDEO_INDEX.md'
    manifest_path = DOCS / 'video_collection_manifest.json'
    assert not output.exists() and not index.exists() and not manifest_path.exists()
    sources = sorted(p for p in RESULTS.rglob('*') if p.is_file() and p.suffix.lower() in SUFFIXES)
    targets = {p: output / '__'.join(p.relative_to(RESULTS).parts) for p in sources}
    assert len(set(targets.values())) == len(sources)
    inputs = {str(p): sha(p) for p in sources}
    for p in [Path(__file__).resolve(), ROOT / 'stability_adapter_2/VIDEO_COLLECTION_PLAN.md']:
        inputs[str(p)] = sha(p)
    for phase in {p.relative_to(RESULTS).parts[0] for p in sources}:
        readme = RESULTS / phase / 'README.md'
        if readme.exists():
            inputs[str(readme)] = sha(readme)
    output.mkdir()
    rows = []
    for source, target in targets.items():
        shutil.copyfile(source, target)
        assert sha(target) == inputs[str(source)] and target.stat().st_size == source.stat().st_size
        command = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                   'stream=duration,avg_frame_rate,nb_frames:format=duration', '-of', 'json', str(target)]
        probe = subprocess.run(command, check=True, capture_output=True, text=True)
        info = json.loads(probe.stdout)
        duration = float(info['format']['duration'])
        relative = source.relative_to(RESULTS)
        phase = relative.parts[0]
        capture = source.parent / 'capture.json'
        report = source.parent / 'report.json'
        actual_time = None
        renderer = '출처 문서 참조'
        if capture.is_file():
            inputs[str(capture)] = sha(capture)
            recorded = json.loads(capture.read_text())
            renderer = recorded.get('renderer', renderer)
            frames = recorded.get('frames', [])
            if frames and 'time_s' in frames[-1]:
                actual_time = frames[-1]['time_s']
        if report.is_file():
            inputs[str(report)] = sha(report)
            record = json.loads(report.read_text())
            if 'simulation_elapsed_s' in record:
                actual_time = record['simulation_elapsed_s']
        if phase in {'best_run_video_v1', 'lower_body_fixed_v1', 'self_collision_v1', 'thigh_palm_support_v1'}:
            renderer = '저장 pose의 source 형상 재구성'
        elif phase in {'finger_grip_hold_v1', 'palm_side_strap_long_v1', 'palm_best_initial_video_v1'}:
            renderer = '저장 Isaac Gym 카메라 영상'
        if phase == 'palm_best_initial_video_v1' and source.name == 'front_view_5s_slowmotion.mp4':
            actual_time = .1
        archive = any(part.startswith(('artifacts_attempt', 'artifacts_pre', 'artifacts_before')) or part in {'render', 'render_v1'} for part in relative.parts)
        if phase == 'best_run_video_v1' and relative.parts[1] == 'videos':
            archive = True
        readme = RESULTS / phase / 'README.md'
        rows.append(dict(source=str(source),copy=str(target),relative_source=str(relative),phase=phase,
                         size=source.stat().st_size,sha256=inputs[str(source)],encoded_duration_s=duration,
                         simulation_end_s=actual_time,renderer=renderer,previous_production=archive,
                         source_readme=str(readme) if readme.exists() else None,ffprobe=info))
    assert all(sha(Path(p)) == value for p, value in inputs.items())
    assert len(list(output.iterdir())) == len(sources) and all(p.suffix.lower() in SUFFIXES for p in output.iterdir())
    def movie_link(row):
        return '[' + Path(row['copy']).name + '](' + row['copy'] + ')'
    text = '# StabilityAdapter 2 영상 모음\n\n'
    text += '원본은 '+str(RESULTS)+' 아래 실험별 폴더에 있다. 영상만 모은 폴더는 ['+str(output)+']('+str(output)+')다.\n\n'
    text += str(len(rows))+'개 전부 원본과 SHA·크기가 같은 복사본이다. 이름은 원본 상대경로를 __로 연결했다. 기존 영상·재시도·이전 제작본도 보존한다. 약'+format(sum(r['size'] for r in rows)/1024/1024,'.2f')+'MiB다. 새 시뮬레이션이나 재인코딩은 하지 않았다.\n\n'
    text += '## 최근 실제 스트랩 영상\n\n'
    for phase, label in [('torso_hold_native_collision_v1','몸통9 PD×2'),('palm_patch_priority_diagnostic_v1','손바닥 옆면 우선'),('strap_video_v1','스트랩 표시 검증')]:
        text += '### '+label+'\n\n'
        for row in rows:
            if row['phase']==phase:
                view='손 근접' if Path(row['copy']).name.endswith('__hands.mp4') else '전신'
                text += '- '+view+': '+movie_link(row)+'\n'
        text += '\n'
    text += '## 전체 목록\n\n파일 길이는 ffprobe로 읽은 재생시간이며 물리 경과시간과 다르다. 특히 slow-motion의5초 재생을5초 물리 실험으로 해석하지 않는다. 물리 종료시각이 —이면 이번 모음에서 해당 field를 확인하지 않았으므로 출처 설명을 따른다. 이전 제작본은 최종본/성공 결과로 간주하지 않는다.\n\n'
    for phase in sorted({r['phase'] for r in rows}):
        group=[r for r in rows if r['phase']==phase]
        text += '### '+phase+'\n\n'
        if group[0]['source_readme']:
            text += '[실험 설명]('+group[0]['source_readme']+':1)\n\n'
        text += '| 영상 | 파일 길이 (초) | 물리 종료시각 (초) | 출처/표시 |\n|---|---:|---:|---|\n'
        for row in group:
            t='—' if row['simulation_end_s'] is None else str(row['simulation_end_s'])
            status=row['renderer']+(' / 이전 제작본' if row['previous_production'] else '')
            text += '| '+movie_link(row)+' | '+format(row['encoded_duration_s'],'.3f')+' | '+t+' | '+status+' |\n'
        text += '\n'
    text += '## 검증\n\n원본'+str(len(rows))+'개·복사본'+str(len(rows))+'개·모든 SHA/크기 일치, ffprobe 전부 성공. 영상 폴더는 영상만 포함한다. Luna 호출은 도구 thread 한도로 실패해 root가 작성했다.\n'
    index.write_text(text)
    manifest_path.write_text(json.dumps(dict(input_sha256_before=inputs,input_sha256_after={p:sha(Path(p)) for p in inputs},rows=rows,native_initializations=0,physics_steps=0),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(videos=len(rows),folder=str(output),index=str(index)),ensure_ascii=False))


if __name__ == '__main__':
    main()
