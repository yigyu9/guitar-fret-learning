"""후속 연구의 평가와 학습 관측을 분리해 읽기 전용으로 요약한다.

완료 보고서 검증은 실행 드라이버가 담당한다. 이 도구는 실행 상태에 기록된
검증된 평가와 원시 학습 로그를 구분하며, 미완료 자료를 성공으로 승격하지 않는다.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/matplotlib-successor-study')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STUDY = Path(__file__).resolve().parents[1]


class Reader:
    def __init__(self):
        self.pins, self.pending, self.errors = {}, [], []

    def read(self, path, lines=False):
        path = Path(path)
        if not path.is_file():
            return [] if lines else {}
        data = path.read_bytes()
        self.pins[str(path)] = hashlib.sha256(data).hexdigest()
        if not lines:
            try:
                return json.loads(data)
            except (ValueError, UnicodeError) as error:
                self.errors.append(dict(path=str(path), error=str(error)))
                return {}
        rows, raw = [], data.splitlines()
        for index, line in enumerate(raw):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except (ValueError, UnicodeError) as error:
                item = dict(path=str(path), line=index + 1)
                if index == len(raw) - 1 and not data.endswith(b'\n'):
                    self.pending.append(item)
                else:
                    self.errors.append(dict(**item, error=str(error)))
        return rows


def episode_counts(rows):
    """두 목표의 접촉·달성은 중복 가능한 개별 집계이며 성공률이 아니다."""
    counts = dict(episodes=len(rows), malformed=0, unsafe=0,
                  contact_any=[0, 0], achieved=[0, 0], clean_seconds=[0., 0.],
                  best_streak_seconds=[0., 0.])
    for row in rows:
        episode = row.get('episode', row)
        values = episode.get('left_note_ledger', {}).get('values', {})
        if any(len(values.get(k, [])) != 2 for k in ('clean', 'contact_time', 'left', 'best_clean_streak')):
            counts['malformed'] += 1
            continue
        termination = episode.get('termination', {})
        counts['unsafe'] += bool(not episode.get('valid') or
            episode.get('song', {}).get('safety_invalidated') or
            termination.get('physical_failure') or termination.get('wrist_failure'))
        for i in range(2):
            counts['contact_any'][i] += values['contact_time'][i] > 0
            counts['achieved'][i] += bool(values['left'][i])
            counts['clean_seconds'][i] += values['clean'][i]
            counts['best_streak_seconds'][i] = max(counts['best_streak_seconds'][i], values['best_clean_streak'][i])
    return counts


def main():
    reader = Reader()
    state = reader.read(STUDY / '진행상황.json')
    cases = {}
    for key, case in state.get('cases', {}).items():
        tasks = {}
        for name, task in state.get('tasks', {}).items():
            if not name.startswith(key + '_train') or not task.get('out'):
                continue
            out = Path(task['out'])
            metrics = reader.read(out / 'J/learning_metrics.jsonl', lines=True)
            episodes = reader.read(out / 'J/episodes.jsonl', lines=True)
            series = []
            for row in metrics:
                recovery = row.get('lr_recovery', {})
                series.append(dict(update=row.get('optimizer_updates', row.get('update_index')),
                    actor_lr=row.get('actor_lr'), analytic_kl=row.get('analytic_kl'),
                    lr_recovery=recovery))
            tasks[name] = dict(completed=task.get('completed') is True,
                failure=task.get('failure'), out=str(out), metrics=series,
                training_observations=episode_counts(episodes))
        cases[key] = dict(input_case=case.get('input_case'), status=case.get('status'),
            finished=case.get('finished', False), arm_std=case.get('arm_std'),
            lr_mode=case.get('lr_mode'), evaluations=case.get('evaluations', {}),
            comparison=case.get('comparison'), selected_video_model=case.get('selected'), tasks=tasks)
    malformed = sum(task['training_observations']['malformed'] for case in cases.values() for task in case['tasks'].values())
    result = dict(schema='successor_analysis.v1', generated_at=datetime.now(timezone.utc).isoformat(),
        completed=bool(state.get('completed') and not reader.errors and not reader.pending and not malformed),
        execution_completed=state.get('completed', False), malformed_episodes=malformed, failure=state.get('failure'),
        parent_selection=state.get('parent_selection'), cases=cases,
        native_checks=state.get('native_candidates', {}),
        evidence_sha256=reader.pins, pending_last_lines=reader.pending, read_errors=reader.errors)
    directory = STUDY / '분석'
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / '결과수치.json'
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(target)
    text = ['# 후속 연구 분석', '', '갱신: ' + result['generated_at'], '',
        '평가는 드라이버가 보고서·체크포인트·입력을 검증한 상태 항목이다. 학습 중 확률적 접촉 관측과 평균 정책 평가는 별도 집계한다.', '',
        '| 과제 | 상태 | 평가 횟수 | 목표별 유지 비율 | 안전 전체 달성 | 오압현 비율 | 엄격 통과 |',
        '|---|---|---:|---|---|---|---|']
    for key, case in cases.items():
        if not case['evaluations']:
            text.append(f"| {key} | {case['status']} | — | — | — | — | 미평가 |")
        for update, entry in sorted(case['evaluations'].items(), key=lambda item: int(item[0])):
            r = entry['result']
            text.append(f"| {key} | {case['status']} | {update} | {r['clean_fraction_by_target']} | {r['safe_success']}/{r['denominator']} | {r['wrong_target_time_ratio']:.3f} | {r['passed']} |")
    text += ['', '단일 seed 결과와 동일 초기 조건의 반복 평가이므로 일반화 성능으로 확대하지 않는다. 대표 영상은 최선 모델의 예시이고, 공통 횟수 비교와 구분한다.', '',
        '미완료 실행의 원시 관측은 결과수치.json의 tasks에 남기며 완료된 성공 실험으로 계산하지 않는다. 시간 보류와 native 미통과는 학습 실패와 구분한다.', '',
        'G1/G2는 실제 압현 경로의 간섭 회피 가능성을 검사하는 참조다. 학습 초기 상태나 정책에 참조 동작을 주입하지 않으므로, 이후 fresh 학습 결과를 참조 동작 전달의 효과라고 해석하지 않는다.', '',
        f"읽기 오류 {len(reader.errors)}개, 마지막 미완성 행 {len(reader.pending)}개. 자세한 원인과 근거 SHA는 결과수치.json에 기록한다."]
    text += ['', '## 실제 물리 재생', '']
    for key, item in result['native_checks'].items():
        text.append(f"- {key}: 통과={item.get('passed')}, 목표별 유지={item.get('fractions')}, 오압현={item.get('wrong_active_union_ratio')}, 관측={item.get('snapshot')}")
    target = directory / '분석.md'
    temporary = target.with_suffix('.md.tmp')
    temporary.write_text('\n'.join(text) + '\n')
    temporary.replace(target)
    if any(case['evaluations'] for case in cases.values()):
        fig, axis = plt.subplots(figsize=(8, 4))
        for key, case in cases.items():
            entries = sorted(case['evaluations'].values(), key=lambda item: item['update'])
            if entries:
                axis.plot([e['update'] for e in entries],
                    [min(e['result']['clean_fraction_by_target']) for e in entries], 'o-', label=key)
        axis.set(xlabel='Training updates', ylabel='Minimum goal clean fraction', ylim=(0, 1.05))
        axis.grid(alpha=.25)
        axis.legend()
        fig.tight_layout()
        fig.savefig(directory / '목표유지비교.png', dpi=160)
        plt.close(fig)
    if reader.errors or malformed:
        sys.exit(1)


if __name__ == '__main__':
    main()
