"""동일601열 신구조의 처음부터 J33 학습 대조군을200회까지만 실행한다.

A와의 비교는 활성 축과 초기 분포가 함께 다른 학습 절차 비교다.
단일 변수의 인과 효과 또는 과거557열 production 모델의 재현으로 해석하지 않는다.
"""
from pathlib import Path
import time

import research as research


def main():
    root = Path(__file__).resolve().parent
    out = root/'index_full33_seed7_v1'
    out.mkdir(exist_ok=False)
    geometry = research.RUNTIME/'guitar_learning/assets/structured_press_v2/catalog.json'
    goal, = [g for g in research.read(geometry)['goals'] if g['finger'] == 'index']
    state = dict(schema='structured_press.seven_hour_progress.v1', finger='index',
        stage='free_v9', seed=7, source=None, source_seal_sha256=research.verify_seal(),
        geometry_sha256=research.digest(geometry), song=goal['song'],
        started_utc=research.utcnow().isoformat(), status='preparing', blocks=[],
        passed=False, consecutive_passes=0, child_pid=None, evaluation_kind='evaluate',
        comparison='fresh601/full33/v9/no phase support versus aligned A4 curriculum; IK arm bias in both')
    research.persist(out, state)
    previous, recent = None, None
    # 기존 단계 승급 규칙을 적용하지 않고 완료된 대조 실험으로만 기록한다.
    try:
        for number in (1, 2):
            state['budget'] = research.training_budget(research.read(root/'budget.json'), recent)
            if not state['budget']['allowed']:
                state['status'] = 'budget_stopped'
                break
            location = out/str(number*100)
            location.mkdir(exist_ok=False)
            train = location/'train'
            command = ['train', '--geometry', str(geometry), '--song', goal['song'],
                '--stage', 'free_v9', '--size', 'large', '--num-envs', '64',
                '--updates', '100', '--seed', '7', '--out', str(train)]
            if previous:
                if research.digest(previous) != state['blocks'][-1]['checkpoint_sha256']:
                    raise ValueError('resume checkpoint changed')
                command += ['--resume', str(previous)]
            started = time.monotonic()
            seconds = research.execute(command, train, out, state)
            if not research.read(train/'report.json')['completed']:
                raise ValueError('incomplete full33 training')
            evaluations = [('final', number*100)]
            if number == 1:
                evaluations.insert(0, ('initial', 0))
            for role, updates in evaluations:
                checkpoint = train/'J'/(role+'.pt')
                evaluation = location/('evaluate_'+role)
                research.execute(['evaluate', '--checkpoint', str(checkpoint), '--num-envs', '32',
                    '--out', str(evaluation)], evaluation, out, state)
                report = research.read(evaluation/'report.json')
                if report['checkpoint_sha256'] != research.digest(checkpoint):
                    raise ValueError('evaluated checkpoint changed')
                values = research.aggregate(evaluation)
                row = dict(updates=updates, checkpoint=str(checkpoint),
                    checkpoint_sha256=research.digest(checkpoint), evaluation=str(evaluation),
                    evaluation_sha256={name: research.digest(evaluation/name)
                        for name in ('report.json', 'episodes.jsonl', 'episode_metadata.json')},
                    summary=values, metrics=values, accepted=None)
                if role == 'initial':
                    state['initial_evaluation'] = row
                else:
                    row.update(train_seconds=seconds, block_seconds=time.monotonic()-started)
                    state['blocks'].append(row)
            previous, recent = train/'J/final.pt', time.monotonic()-started
            state['status'] = 'block_complete'
            research.persist(out, state)
        else:
            state['status'] = 'completed_comparison_not_stage_promotion'
    except research.BudgetStop as error:
        state.update(status='budget_stopped', partial_block=True, stop_reason=str(error))
    except BaseException as error:
        state.update(status='error', failure=type(error).__name__+': '+str(error))
        raise
    finally:
        research.persist(out, state)


if __name__ == '__main__':
    main()
