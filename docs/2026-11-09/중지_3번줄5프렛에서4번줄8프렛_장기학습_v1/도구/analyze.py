"""장기 전환 연구의 원시 로그를 읽고 학습·평가·실행 오류를 구분한다.

완료 여부와 체크포인트 검증은 드라이버가 담당한다. 확률 학습의 달성과
고정 모델의 평균/확률 평가를 섞지 않으며, 큰 에피소드 파일은 줄 단위로 읽는다.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib-long-transition')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STUDY = Path(__file__).resolve().parents[1]


class Reader:
    def __init__(self):
        self.pins, self.pending, self.errors = {}, [], []

    def document(self, path):
        path = Path(path)
        if not path.exists():
            return {}
        data = path.read_bytes()
        self.pins[str(path)] = hashlib.sha256(data).hexdigest()
        try:
            return json.loads(data)
        except (ValueError, UnicodeError) as error:
            self.errors.append(dict(path=str(path), error=str(error)))
            return {}

    def rows(self, path):
        path = Path(path)
        if not path.exists():
            return
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for number, line in enumerate(stream, 1):
                digest.update(line)
                if not line.strip():
                    continue
                try:
                    yield json.loads(line)
                except (ValueError, UnicodeError) as error:
                    if not line.endswith(b'\n') and not stream.peek(1):
                        self.pending.append(dict(path=str(path), line=number))
                    else:
                        self.errors.append(dict(path=str(path), line=number, error=str(error)))
        self.pins[str(path)] = digest.hexdigest()


def safe(episode):
    t = episode.get('termination', {})
    return bool(episode.get('valid') and not episode.get('song', {}).get('safety_invalidated')
        and not t.get('physical_failure') and not t.get('wrist_failure'))


def observations(rows):
    result = dict(episodes=0, malformed=0, unsafe=0, contact=[0, 0], achieved=[0, 0],
                  both_safe=0, clean_seconds=[0., 0.], reward_components={})
    for row in rows:
        e = row.get('episode', row)
        result['episodes'] += 1
        v = e.get('left_note_ledger', {}).get('values', {})
        if any(len(v.get(k, [])) != 2 for k in ('clean', 'left', 'contact_time')):
            result['malformed'] += 1
            continue
        result['unsafe'] += not safe(e)
        result['both_safe'] += bool(safe(e) and e['song']['stage_success'] and all(v['left']))
        for i in (0, 1):
            result['contact'][i] += v['contact_time'][i] > 0
            result['achieved'][i] += bool(v['left'][i])
            result['clean_seconds'][i] += v['clean'][i]
        for key, value in e.get('reward_components', {}).items():
            result['reward_components'][key] = result['reward_components'].get(key, 0.) + value
    return result


def atomic(path, text):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(text)
    temp.replace(path)


def main():
    reader = Reader()
    state = reader.document(STUDY / '진행상황.json')
    segments, metrics = [], []
    for segment in state.get('training_segments', []):
        out = Path(segment['out']) / 'J'
        obs = observations(reader.rows(out / 'episodes.jsonl'))
        series = []
        for row in reader.rows(out / 'learning_metrics.jsonl'):
            series.append(dict(update=row['optimizer_updates'], actor_lr=row['actor_lr'],
                kl=row['analytic_kl'], lr_recovery=row.get('lr_recovery', {})))
        segments.append(dict(**segment, observations=obs, recorded_updates=len(series)))
        metrics.extend(series)
    evaluations = []
    for entry in state.get('evaluations', []):
        item = dict(entry)
        item['raw_observations'] = observations(reader.rows(Path(entry['out']) / 'episodes.jsonl'))
        evaluations.append(item)
    malformed = sum(s['observations']['malformed'] for s in segments) + sum(e['raw_observations']['malformed'] for e in evaluations)
    report = dict(schema='middle_cross_string_long_analysis.v1',
        generated_at=datetime.now(timezone.utc).isoformat(), execution_completed=state.get('completed', False),
        completed=bool(state.get('completed') and not reader.errors and not reader.pending and not malformed),
        status=state.get('status'), failure=state.get('failure'), training_plan=state.get('training_plan', {}),
        native_validation=state.get('native_validation'), benchmark=state.get('benchmark', {}),
        segments=segments, metrics=metrics, evaluations=evaluations, videos=state.get('videos', {}),
        pending_last_lines=reader.pending, read_errors=reader.errors, malformed_episodes=malformed,
        evidence_sha256=reader.pins)
    directory = STUDY / '분석'
    directory.mkdir(parents=True, exist_ok=True)
    atomic(directory / '결과수치.json', json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    lines = ['# 중지 줄·프렛 전환 장기 학습', '', '갱신: ' + report['generated_at'], '',
        '과제: 중지 3번 줄 5프렛 → 4번 줄 8프렛. 보상·제어·성공 판정은 유지한다.', '',
        '실행 상태: ' + str(report['status']), '',
        '## 고정 모델 평가', '',
        '| 업데이트 | 평가 방식 | A/B 유지 비율 | 두 음 안전 달성 | 오압현 비율 | 엄격 통과 |',
        '|---:|---|---|---|---|---|']
    for e in evaluations:
        r = e.get('result', {})
        lines.append(f"| {e['update']} | {e['mode']} | {r.get('clean_fraction_by_target')} | {r.get('safe_success')}/{r.get('denominator')} | {r.get('wrong_target_time_ratio')} | {r.get('passed')} |")
    lines += ['', '## 학습 중 관측', '',
        '| 누적 업데이트 | 종료 에피소드 | A/B 접촉 | A/B 달성 | 두 음 안전 달성 | 무효/실패 |',
        '|---:|---:|---|---|---:|---:|']
    for segment in segments:
        v = segment['observations']
        lines.append(f"| {segment.get('cumulative_updates')} | {v['episodes']} | {v['contact']} | {v['achieved']} | {v['both_safe']} | {v['unsafe']} |")
    lines += ['', '학습 중 달성은 원장 기준이며, 전체 음 길이 유지나 정확한 시작·해제를 보장하지 않는다.',
        '학습 중에는 정책 가중치가 계속 변한다. 탐색 유무의 직접 비교는 동일 체크포인트의 mean/stochastic 평가로 판단한다.',
        '평균 평가는 동일 준비 상태의 반복이며 독립 학습 seed가 아니다. 한 seed의 결과를 일반적 수렴이나 모든 목표의 물리 가능성으로 확대하지 않는다.',
        '접근 보상은 잠재 품질의 차이와 종료 정산이다. 원시 합의 크기만으로 다른 보상과 비교하지 않는다.',
        f'읽기 오류 {len(reader.errors)}개, 미완성 마지막 행 {len(reader.pending)}개, 손상 원장 {malformed}개. 실패/보류 원문은 실행 디렉토리에 보존한다.']
    atomic(directory / '분석.md', '\n'.join(lines) + '\n')
    if metrics or evaluations:
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
        for mode, style in (('mean', 'o-'), ('stochastic', 's--')):
            entries = [e for e in evaluations if e['mode'] == mode]
            if entries:
                axes[0].plot([e['update'] for e in entries],
                    [min(e['result']['clean_fraction_by_target']) for e in entries], style, label=mode)
        axes[0].set(title='Minimum goal clean fraction', xlabel='Cumulative updates', ylim=(0, 1.05))
        if evaluations:
            axes[0].legend()
        if metrics:
            axes[1].plot([m['update'] for m in metrics], [m['actor_lr'] for m in metrics])
        axes[1].set(title='Accepted actor learning rate', xlabel='Cumulative updates')
        for axis in axes:
            axis.grid(alpha=.25)
        fig.savefig(directory / '학습경과.png', dpi=160)
        plt.close(fig)
    if reader.errors or malformed:
        sys.exit(1)


if __name__ == '__main__':
    main()
