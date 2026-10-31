"""개별·조합 연구의 완료된 근거만 CPU에서 집계한다. 학습 설정은 바꾸지 않는다."""
import argparse
from collections import defaultdict
import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from guitar_learning.training.training_log_io import iter_episode_rows


def read(path):
    return json.loads(path.read_text())


def atomic(path, text):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(text)
    os.replace(str(temporary), str(path))


def report(root):
    source = read(root / 'study_results.json')
    rows = source if isinstance(source, list) else source['results']
    selection = source.get('selection') if isinstance(source, dict) else None
    if (root / 'selection.json').exists():
        selection = read(root / 'selection.json')
    results = []
    for row in rows:
        item = dict(row)
        run = root / 'runs' / row['run_id']
        train = run / 'train/J'
        evaluation = run / 'evaluation'
        tr = read(train / 'report.json') if (train / 'report.json').exists() else None
        ev = read(evaluation / 'report.json') if (evaluation / 'report.json').exists() else None
        item['verified_train_complete'] = bool(tr and tr.get('completed') and not tr.get('failure'))
        item['verified_evaluation_complete'] = bool(ev and ev.get('completed') and not ev.get('failure'))
        item['failure'] = row.get('failure') or (tr or {}).get('failure') or (ev or {}).get('failure')
        item['train_scope'] = {key: (tr or {}).get(key) for key in
                               ['updates_in_run', 'transitions', 'wall_s', 'exposure_transitions']}
        settings = (tr or {}).get('settings', {})
        item['train_scope'].update({key: settings.get(key) for key in ['num_envs', 'horizon', 'seed', 'size']})
        item['evaluation_scope'] = (ev or {}).get('scope')
        item['matches_planned_training_budget'] = all(item['train_scope'].get(key) == value for key, value in
            [('updates_in_run', 200), ('transitions', 6553600), ('num_envs', 1024), ('horizon', 32), ('size', 'large')])
        lr = dict(first=None, last=None, changes=0, decreases=0, increases=0, recovered_updates=0,
                  kl_retry_attempts=0, logged_updates=0)
        previous_lr = settings.get('ppo', {}).get('actor_lr')
        if (train / 'learning_metrics.jsonl').exists():
            with (train / 'learning_metrics.jsonl').open() as stream:
                for line in stream:
                    metric = json.loads(line)
                    value = float(metric['actor_lr'])
                    if not math.isfinite(value):
                        raise ValueError('Nonfinite actor_lr: ' + row['run_id'])
                    if lr['first'] is None:
                        lr['first'] = value
                    if previous_lr is not None and value != previous_lr:
                        lr['changes'] += 1
                        lr['decreases'] += value < previous_lr
                        lr['increases'] += value > previous_lr
                    previous_lr = value
                    lr['last'] = value
                    lr['logged_updates'] += 1
                    lr['kl_retry_attempts'] += metric.get('kl_retries', 0)
                    lr['recovered_updates'] += bool(metric.get('diagnostics', {}).get(
                        'research_learning_rate', {}).get('recovered', False))
        item['learning_rate'] = lr
        fingers = {name: defaultdict(float) for name in ['index', 'middle', 'ring', 'pinky']}
        rewards, n = defaultdict(float), 0
        if item['verified_evaluation_complete']:
            for record in iter_episode_rows(evaluation):
                episode = record['episode']
                n += 1
                for name, metric in zip(fingers, episode['left_curriculum']['finger_metrics']):
                    count = metric['target_count']
                    fingers[name]['target_opportunities'] += count
                    for key in ['contact_fraction', 'success_fraction', 'near_fraction']:
                        fingers[name][key + '_weighted_sum'] += metric[key] * count
                for key, value in episode['reward_components'].items():
                    rewards[key] += value
            if n != ev['episodes']:
                raise ValueError('Evaluation count mismatch: ' + row['run_id'])
        item['finger_metrics'] = {name: dict(target_opportunities=f['target_opportunities'], **{
            key: f[key + '_weighted_sum'] / f['target_opportunities'] if f['target_opportunities'] else None
            for key in ['contact_fraction', 'success_fraction', 'near_fraction']}) for name, f in fingers.items()}
        item['evaluation_reward_mean_episode_total'] = {key: value / n for key, value in rewards.items()}
        item['evaluated_episodes_restored'] = n
        results.append(item)
    text = ['# 개별·조합 연구 결과', '',
            '이 문서는 현재까지 저장된 실행 상태를 반영한다. 진행 중·실패·평가 미완료를 성공으로 취급하지 않는다.', '',
            '계획: large / 1024환경 / H32 / 각200업데이트(6,553,600전이), 동일 seed·노출 일정. 실제 반복·전이·시간은 아래에 별도 기록한다. 평가 실패 환경도 분모에 포함한다.', '',
            'seed7은 선별이고 seed17의 기준/선택 비교는 추가 확인이다. 두 seed만으로 일반적 우위를 확정하지 않으며 연구 선택은 기본 설정 반영을 뜻하지 않는다.', '',
            '|실행|요인|학습/평가 완료|평균 달성 음|물리/손목 종료|평가 에피소드|실제 반복/전이/학습시간|',
            '|---|---|---|---:|---|---:|---|']
    for r in results:
        scope = r['train_scope']
        hours = '미확인' if scope['wall_s'] is None else '%.2fh' % (scope['wall_s'] / 3600)
        score = r.get('mean_achieved_notes') if r['verified_evaluation_complete'] else None
        text.append('|%s|%s|%s/%s|%s|%s/%s|%s|%s/%s/%s|' % (
            r['run_id'], r.get('factors'), r['verified_train_complete'], r['verified_evaluation_complete'],
            '미확인' if score is None else '%.4f' % score, r.get('physical_failures'), r.get('wrist_failures'),
            r.get('episodes'), scope['updates_in_run'], scope['transitions'], hours))
    text += ['', '## 학습률과 손가락별 결과', '',
             '손가락 비율은 해당 손가락의 목표 음 개수로 가중한다. 기하·하중 기반 접촉/달성 판정이며 음향 성공을 뜻하지 않는다. 평가 보상은 에피소드 총점의 평균이며 전이당 보상과 혼합하지 않는다.', '']
    for r in results:
        text += ['### ' + r['run_id'], '', '학습률 진단: `%s`' % json.dumps(r['learning_rate'], ensure_ascii=False)]
        text.append('계획 학습 예산 일치: `%s`; 평가 범위: `%s`.' % (r['matches_planned_training_budget'], r['evaluation_scope']))
        if 'adaptive_lr' in r.get('factors', []) and not r['learning_rate']['recovered_updates'] and not r['learning_rate']['changes']:
            text.append('학습률 감소·회복이 관측되지 않았다. 이200회 결과만으로 학습률 변경의 효과를 판단할 수 없다.')
        text += ['', '|손가락|목표 음 기회|접촉 비율|달성 비율|', '|---|---:|---:|---:|']
        for name, f in r['finger_metrics'].items():
            text.append('|%s|%g|%s|%s|' % (name, f['target_opportunities'], f['contact_fraction'], f['success_fraction']))
        text += ['', '평가 보상별 평균 총점: `%s`' % json.dumps(r['evaluation_reward_mean_episode_total'], ensure_ascii=False),
                 '', '실행 실패: `%s`' % r.get('failure'), '']
    text += ['## 해석 범위', '', '200회는 짧은 선별이다. 초기 조건·실제 학습 예산·평가 범위가 동일한 실행끼리 비교해야 한다. 단일 미세 향상, 미발동 요인, 조합 상호작용을 구분한다.', '',
             '권장 후보 판단 기준은 두 seed에서 각각 기준 대비 평균 달성 음 +0.25 이상, 실패 횟수는 기준 대비 +2/128 이내인 경우다. 실제 채택 판단은 선택 기록을 따르며 이 문서는 기본 설정을 변경하지 않는다.', '',
             '선택 기록: `%s`' % json.dumps(selection, ensure_ascii=False), '', '![평가 평균 달성 음](performance.png)', '']
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    valid = [r for r in results if r['verified_evaluation_complete'] and r.get('mean_achieved_notes') is not None]
    fig, ax = plt.subplots(figsize=(max(8, len(valid) * .8), 5))
    ax.bar([r['run_id'] for r in valid], [r['mean_achieved_notes'] for r in valid])
    ax.set(ylabel='Mean achieved notes / full-song episode', title='Completed evaluations (failures included)')
    ax.tick_params(axis='x', rotation=45)
    fig.tight_layout()
    fig.savefig(str(root / 'performance.tmp.png'), dpi=140)
    plt.close(fig)
    os.replace(str(root / 'performance.tmp.png'), str(root / 'performance.png'))
    atomic(root / 'analysis_summary.json', json.dumps(dict(results=results, selection=selection), ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    atomic(root / 'RESULTS.md', '\n'.join(text))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True, type=Path)
    report(parser.parse_args().root.resolve())
