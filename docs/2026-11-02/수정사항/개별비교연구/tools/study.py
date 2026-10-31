"""같은 예산의 단독 요인 → 사전 지정 조합 → 새 seed 확인을 순차 실행한다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time


MODULE = 'guitar_learning.tool.experiments.finger_ablation'
SINGLES = [('baseline', []), ('lr', ['adaptive_lr']), ('exploration', ['exploration']),
           ('separate', ['separate']), ('preparation', ['preparation']), ('geometry', ['geometry'])]
PAIRS = [('lr_exploration', ['adaptive_lr', 'exploration']),
         ('preparation_geometry', ['preparation', 'geometry'])]


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    repo = Path.cwd()
    result = dict(schema='guitar_learning.finger_ablation_study.v1', results=[], selection={})
    state = dict(completed=False, phase='starting', started_at=now(), default_changed=False)
    seal = json.loads((root/'active_sources_sealed.json').read_text())
    tool_seal = json.loads((root/'tools_sealed.json').read_text())

    def check_sources():
        if any(hashlib.sha256((root/p).read_bytes()).hexdigest() != h
               for p, h in tool_seal.items()):
            raise RuntimeError('study tool source changed')
        actual = {str(p.relative_to(repo)) for p in (repo/'guitar_learning').rglob('*.py')
                  if 'archive' not in p.relative_to(repo/'guitar_learning').parts}
        if actual != set(seal) or any(hashlib.sha256((repo/p).read_bytes()).hexdigest() != h
                                     for p, h in seal.items()):
            raise RuntimeError('active source set/hash changed; study stopped without loosening pins')

    def status(**changes):
        state.update(changes, updated_at=now())
        write(root/'status.json', state)
        write(root/'study_results.json', result)

    def report():
        command = [sys.executable, '-B', str(root/'tools/report_study.py'), '--root', str(root)]
        with (root/'reporter.log').open('a') as stream:
            subprocess.run(command, check=True, stdout=stream, stderr=subprocess.STDOUT)

    def execute(label, command, folder):
        check_sources()
        status(phase=label)
        with (folder/(label+'.log')).open('x') as stream:
            subprocess.run([sys.executable, '-B', '-m', MODULE]+command, check=True,
                           stdout=stream, stderr=subprocess.STDOUT)
        check_sources()

    def trial(label, factors, seed):
        identity = label+'_s'+str(seed)
        folder = root/'runs'/identity
        folder.mkdir(parents=True, exist_ok=False)
        row = dict(run_id=identity, factors=factors, seed=seed, updates=200,
                   train_complete=False, evaluation_complete=False, failure=None)
        write(folder/'experiment.json', row)
        result['results'].append(row)
        begun = time.monotonic()
        try:
            execute('train_'+identity, ['train', '--updates', '200', '--num-envs', '1024',
                '--size', 'large', '--seed', str(seed), '--out', str(folder/'train'),
                '--factors']+factors, folder)
            training = json.loads((folder/'train/J/report.json').read_text())
            if not training['completed'] or training['updates_in_run'] != 200:
                raise RuntimeError('incomplete fixed-budget training')
            row['train_complete'] = True
            row['training_wall_s'] = training['wall_s']
            execute('evaluate_'+identity, ['evaluate', '--checkpoint', str(folder/'train/J/final.pt'),
                '--num-envs', '128', '--out', str(folder/'evaluation')], folder)
            evaluation = json.loads((folder/'evaluation/report.json').read_text())
            if not evaluation['completed'] or evaluation['episodes'] != 128:
                raise RuntimeError('incomplete fixed128 full-song evaluation')
            summary = evaluation['summary']
            row.update(evaluation_complete=True, mean_achieved_notes=summary['mean_left_success_count'],
                physical_failures=summary['physical_failure'], wrist_failures=summary['wrist_failure'],
                timeline_complete=summary['timeline_complete'], episodes=evaluation['episodes'])
        except subprocess.CalledProcessError as error:
            row['failure'] = str(error)
            if identity.startswith('baseline'):
                raise
            # 개별 조건의 실패도 결과다. 소스 변경 오류는 아래 확인에서 연구 전체를 멈춘다.
            check_sources()
        finally:
            row['wall_s'] = time.monotonic()-begun
            write(folder/'experiment.json', row)
            status(last_finished=identity)
            report()
        return row

    def acceptable(candidate, baseline, improvement=.25):
        return (candidate['evaluation_complete'] and baseline['evaluation_complete']
            and candidate['mean_achieved_notes'] >= baseline['mean_achieved_notes']+improvement
            and candidate['episodes']-candidate['timeline_complete'] <=
                baseline['episodes']-baseline['timeline_complete']+2)

    try:
        baseline = None
        for label, factors in SINGLES+PAIRS:
            row = trial(label, factors, 7)
            if label == 'baseline': baseline = row
        candidates = [r for r in result['results'] if acceptable(r, baseline)]
        # 단독 개선이 약해도 상호작용은 있을 수 있어 두 조합은 사전 지정해 검사한다.
        if candidates:
            union = sorted({f for row in candidates for f in row['factors']})
            if len(union) >= 2 and not any(set(r['factors']) == set(union) for r in result['results']):
                row = trial('combined', union, 7)
                if acceptable(row, baseline): candidates.append(row)
        if not candidates:
            result['selection'] = dict(phase='complete', confirmed=False,
                reason='no candidate cleared descriptive improvement and safety screen',
                recommended_factors=[], default_changed=False)
        else:
            best = max(candidates, key=lambda row:row['mean_achieved_notes'])
            result['selection'] = dict(phase='confirming', screen_winner=best['run_id'],
                recommended_factors=best['factors'], confirmed=False, default_changed=False)
            write(root/'selection.json', result['selection'])
            report()
            reference = trial('baseline', [], 17)
            confirmation = trial('selected', best['factors'], 17)
            confirmed = acceptable(confirmation, reference)
            result['selection'].update(phase='complete', confirmed=confirmed,
                confirmation_candidate=confirmation['run_id'], confirmation_baseline=reference['run_id'],
                reason='positive in both tested training seeds' if confirmed else 'not reproduced on second seed',
                adoption='reviewed research recipe only; production default unchanged')
            if confirmed:
                write(root/'recommended_recipe.json', dict(schema='guitar_learning.research_recipe.v1',
                    factors=best['factors'], training=dict(size='large', num_envs=1024, horizon=32),
                    evidence=[best['run_id'], confirmation['run_id']], limited_budget_updates=200,
                    limitation='two-seed early screening; long-run convergence not established'))
        write(root/'selection.json', result['selection'])
        status(completed=True, phase='complete', finished_at=now())
        report()
    except BaseException as error:
        status(phase='failed', failure=repr(error), finished_at=now())
        raise


if __name__ == '__main__':
    main()
