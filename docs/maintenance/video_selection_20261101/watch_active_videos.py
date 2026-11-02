"""학습이 완전히 끝난 뒤 공개 영상만 손/전신 한 쌍으로 정리한다.

원본 렌더·체크포인트·학습 상태는 수정하지 않는다. 완료·봉인·영상 SHA가
불확실하면 아무것도 삭제하지 않고 별도 정리 보고서에 실패를 남긴다.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import signal
import time

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_BASE = ROOT/'docs/2026-11-02/압현실험/중지6에서8프렛_환경수비교_20261101'


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def direct_file(path, parent):
    """직접 자식 일반 파일만 허용한다. 심볼릭 링크를 따라 삭제하지 않는다."""
    path = Path(path)
    if not path.is_absolute() or path.is_symlink() or path.parent.resolve() != parent.resolve() or not path.is_file():
        raise ValueError('허용 위치 밖 또는 일반 파일 아님: '+str(path))
    return path


def inside(path, parent):
    return parent.resolve() in path.resolve().parents


def checked(path, expected):
    if sha(path) != expected:
        raise ValueError('SHA 불일치: '+str(path))


def ready(base):
    pipeline = read(base/'pipeline_v2.json')
    state = read(base/'learning_v1/progress.json')
    for data in (pipeline, state):
        if data.get('status') in ('failed', 'interrupted', 'cancelled'):
            raise RuntimeError('학습 중단: 공개 영상 원본 보존')
    if pipeline.get('status') != 'complete' or state.get('status') != 'complete':
        return None
    if read(base/'learning_v1/SOURCE_VERIFICATION.json').get('unchanged') is not True:
        raise ValueError('학습 소스 불변 검증 실패')
    return state


def episode_quality(episode):
    values = episode['left_note_ledger']['values']
    term = episode['termination']
    successes = values['left']
    clean = values['clean']
    valid = episode.get('valid') is True and term.get('physical_failure') is False and term.get('wrist_failure') is False
    success = valid and len(successes) == 2 and all(v is True for v in successes)
    full = success and len(clean) == 2 and all(v >= 1.5-1e-6 for v in clean)
    return dict(success=success, full_duration=full, valid=valid, left=successes, clean_s=clean)


def final_score(state, checkpoint):
    rows = [row['metrics'] for row in state['results'].values()
            if row.get('checkpoint') == checkpoint and row.get('mode') == 'mean'
            and row.get('tag') in ('best_final', 'best_repeat', 'last_final', 'last_repeat')]
    if len(rows) < 2 or any(m.get('episodes') != 128 for m in rows):
        raise ValueError('최종 반복 mean128 평가 부족: '+checkpoint)
    return tuple(sum(m[key]/128 for m in rows)/len(rows)
                 for key in ('full_duration_pair', 'AB', 'on_time_with_previous_tail'))


def select(base, state):
    public = base/'동영상'
    if public.is_symlink() or public.resolve().parent != base.resolve():
        raise ValueError('공개 디렉토리 심볼릭 링크 또는 경로 이탈')
    videos = state['videos']
    if not videos:
        raise ValueError('완료 상태에 공개 영상 목록 없음')
    protected = [base/'pipeline_v2.json', base/'learning_v1/progress.json', base/'learning_v1/SOURCE_VERIFICATION.json']
    paths, groups = set(), {}
    for item in videos:
        path = direct_file(item['path'], public)
        if path in paths or path.suffix != '.mp4':
            raise ValueError('중복 또는 MP4 외 공개 영상')
        paths.add(path)
        checked(path, item['sha256'])
        matches = []
        for label, job in state['jobs'].items():
            if job.get('operation') != 'render' or job.get('status') != 'complete':
                continue
            folder = Path(job['out'])
            if folder.is_symlink() or folder.resolve().parent != (base/'learning_v1/jobs').resolve():
                raise ValueError('렌더 경로 이탈')
            for view in ('hand', 'fullbody'):
                source = folder/(view+'.mp4')
                if source.is_file() and not source.is_symlink() and sha(source) == item['sha256']:
                    report_path = folder/'report.json'
                    report = read(report_path)
                    if report.get('checkpoint') == item['checkpoint']:
                        matches.append((label, folder, view, source, report))
        # best와 last가 같은 모델일 때 원본 파일 SHA까지 같을 수 있다.
        # 공개 파일명의 seed/best/last와 render 작업명으로 일치하는 원본을 선택한다.
        named = [m for m in matches if ('_'+('best' if '_best_' in path.name else 'last')+'_render') in m[0]
                 and ('seed'+m[0].split('_')[0][1:]+'_') in path.name]
        if len(named) != 1:
            raise ValueError('공개 영상 원본이 유일하지 않음: '+str(path))
        label, folder, view, source, report = named[0]
        if report.get('completed') is not True or report.get('lifecycle_verified') is not True or report.get('policy_unchanged') is not True or report.get('source_checkpoint_pins_validated') is not True or any(report.get(k) for k in ('failure', 'changed_inputs', 'missing_import_pins', 'cleanup_errors')):
            raise ValueError('렌더 검증 실패: '+str(folder))
        cp = Path(item['checkpoint'])
        if cp.is_symlink() or not inside(cp, base/'learning_v1/jobs'):
            raise ValueError('모델 경로 이탈')
        checked(cp, report['checkpoint_sha256'])
        evidence = state['jobs'][label].get('evidence')
        required = (folder/'report.json', folder/'hand.mp4', folder/'fullbody.mp4')
        if not isinstance(evidence, dict) or any(str(p) not in evidence for p in required):
            raise ValueError('봉인 보고서/손/전신 evidence 누락: '+str(folder))
        for evidence_path, digest in evidence.items():
            evidence_path = Path(evidence_path)
            if not inside(evidence_path, base):
                raise ValueError('증거 경로 이탈')
            checked(evidence_path, digest)
        episode_path = folder/'episode_env0000.json'
        episode = read(episode_path)
        if report.get('episode') != episode:
            raise ValueError('봉인 렌더 보고서와 env0 기록 불일치: '+str(folder))
        quality = episode_quality(episode)
        group = groups.setdefault(label, dict(label=label, checkpoint=str(cp), quality=quality,
                                             score=final_score(state, str(cp)), videos=[]))
        group['videos'].append(dict(path=str(path), sha256=item['sha256'], source=str(source), view=view))
        protected += [cp, source, folder/'report.json', episode_path]
    actual = set(public.iterdir())
    if actual != paths:
        raise ValueError('공개 폴더 파일과 봉인 영상 목록 불일치')
    if any(sorted(v['view'] for v in g['videos']) != ['fullbody', 'hand'] for g in groups.values()):
        raise ValueError('손/전신 영상 쌍 불완전')
    winner = max(groups.values(), key=lambda g: (g['quality']['success'], g['quality']['full_duration'], *g['score'], g['label']))
    keep = winner['videos']
    retained = {v['path'] for v in keep}
    remove = [v for g in groups.values() for v in g['videos'] if v['path'] not in retained]
    return dict(selected=winner, kept=keep, removed=remove,
                classification='압현 성공' if winner['quality']['success'] else '실패 진단 대표 영상; 성공으로 분류하지 않음',
                reason='실제 env0 두 음 달성·정상 종료, 전 음길이 유지 우선; 이후 반복 mean128의 full/AB/on-time 비율 순'), {str(p): sha(p) for p in set(protected)}


def cleanup(base, out=None):
    state = ready(base)
    if state is None:
        return None
    plan, protected = select(base, state)
    plan.update(status='validated', deleted=[], protected_sha256=protected)
    if out is not None:
        save(out, plan)
    # 검증을 모두 끝낸 후 공개 사본/하드링크만 삭제한다.
    for item in plan['removed']:
        direct_file(item['path'], base/'동영상')
        checked(Path(item['path']), item['sha256'])
    for item in plan['removed']:
        Path(item['path']).unlink()
        plan['deleted'].append(item['path'])
        if out is not None:
            save(out, plan)
    for path, digest in protected.items():
        checked(Path(path), digest)
    plan.update(status='complete', original_outputs_unchanged=True, protected_sha256=protected)
    return plan


def save(out, report):
    report['updated_at'] = datetime.now(timezone.utc).isoformat()
    target = out/'active_video_cleanup.json'
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(target)
    lines = ['# 진행 중 실험 공개 영상 정리', '', '상태: '+report['status'], '',
             report.get('classification', report.get('error', '학습 및 봉인 검증 완료를 기다리는 중'))]
    for key, title in [('kept', '남긴 영상'), ('removed', '제거한 공개 링크')]:
        if key in report:
            lines += ['', title+':', '']+[f"- {v['path']} (SHA256 {v['sha256']})" for v in report[key]]
    (out/'active_video_cleanup.md').write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    target = args.out/'active_video_cleanup.json'
    if target.exists():
        raise FileExistsError('기존 감시/정리 기록 보존: '+str(target))
    def stop(signum, frame):
        raise KeyboardInterrupt('종료 신호 '+str(signum))
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    report = dict(status='waiting', base=str(args.base))
    save(args.out, report)
    try:
        while True:
            result = cleanup(args.base, args.out)
            if result is not None:
                report = result
                break
            time.sleep(30)
    except BaseException as error:
        report = read(target)
        report.update(status='interrupted' if isinstance(error, KeyboardInterrupt) else 'failed',
                      error=repr(error), base=str(args.base), note='불확실한 자료는 보존; 부분 삭제 여부는 deleted 목록 및 실제 공개 폴더와 대조')
        raise
    finally:
        save(args.out, report)


if __name__ == '__main__':
    main()
