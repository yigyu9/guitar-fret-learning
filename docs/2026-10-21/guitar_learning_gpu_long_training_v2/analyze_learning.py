"""Streaming analysis of committed GPU updates; safe to rerun during training."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path


def json_document(path):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def lines(path, audit):
    """An unfinished last line is never counted, even if it parses as JSON."""
    if not path.exists():
        return
    with path.open() as stream:
        for number, line in enumerate(stream, 1):
            if not line.endswith('\n'):
                audit['incomplete_last_lines_skipped'] += 1
                break
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError('%s:%d: malformed complete JSONL line' % (path, number)) from error


class Mean:
    def __init__(self):
        self.total = self.weight = 0.
        self.count = 0
        self.minimum = self.maximum = self.first = self.last = None

    def add(self, value, weight=1):
        if value is None:
            return
        value = float(value)
        if not math.isfinite(value) or weight <= 0:
            return
        self.total += value*weight
        self.weight += weight
        self.count += 1
        if self.first is None:
            self.first = value
        self.last = value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)

    def merge(self, other):
        if not other.count:
            return
        if self.first is None:
            self.first = other.first
        self.last = other.last
        self.total += other.total
        self.weight += other.weight
        self.count += other.count
        self.minimum = other.minimum if self.minimum is None else min(self.minimum, other.minimum)
        self.maximum = other.maximum if self.maximum is None else max(self.maximum, other.maximum)

    def result(self):
        return dict(mean=self.total/self.weight if self.weight else None, observations=self.count,
                    weight=self.weight, min=self.minimum, max=self.maximum, first=self.first, last=self.last)


class Group:
    def __init__(self):
        self.updates = self.transitions = self.episodes = self.steps = 0
        self.timeline = self.failures = self.successes = self.safe_full = 0
        self.note_targets = self.note_left = self.full_targets = self.full_left = 0
        self.reasons, self.stages = Counter(), Counter()
        self.means = {}
        self.retry_count = self.updates_with_retries = 0
        self.first_update = self.last_update = None

    def add_value(self, name, value, weight=1):
        self.means.setdefault(name, Mean()).add(value, weight)

    def update(self, row):
        index, n = row['update_index'], row['transitions']
        self.updates += 1
        self.transitions += n
        self.first_update = index if self.first_update is None else min(index, self.first_update)
        self.last_update = index if self.last_update is None else max(index, self.last_update)
        for name in ('mean_reward', 'mean_cost'):
            self.add_value(name, row.get(name), n)
        for name in ('analytic_kl', 'max_attempted_kl', 'actor_lr', 'cost_weight', 'collection_s', 'update_s'):
            self.add_value(name, row.get(name))
        self.retry_count += row.get('kl_retries', 0)
        self.updates_with_retries += row.get('kl_retries', 0) > 0
        diagnostic = row.get('diagnostics', {})
        for branch in ('actor_accepted', 'value'):
            mini = diagnostic.get('minibatches', {}).get(branch, {})
            for name, value in mini.get('sample_weighted_mean', {}).items():
                self.add_value(branch+'.'+name, value, mini.get('sample_visits', 0))
        post = diagnostic.get('post_update', {})
        self.add_value('clip_fraction', post.get('clip_fraction'), n)
        active = post.get('active_distribution', {})
        self.add_value('policy_std', active.get('std', {}).get('mean'), n)
        self.add_value('action_saturation_fraction', active.get('collected_action_saturation_fraction'), n)
        for critic, value in post.get('critics', {}).items():
            self.add_value(critic+'_critic_mse', value.get('mse'), n)
            # A mean of per-update EV values is not a pooled explained variance.
            self.add_value(critic+'_critic_explained_variance_mean_of_updates', value.get('explained_variance'))
        curriculum = row.get('left_curriculum', {})
        self.add_value('curriculum_progress', curriculum.get('progress'))
        if 'stage' in curriculum:
            self.stages[curriculum['stage']] += 1
        for episode in row.get('completed_episodes', []):
            self.episode(episode)

    def episode(self, row):
        self.episodes += 1
        steps = row.get('steps', 0)
        self.steps += steps
        self.timeline += row.get('reason') == 'timeline_complete'
        self.failures += row.get('reason') == 'terminal_failure'
        song, curriculum = row.get('song', {}), row.get('left_curriculum', {})
        full_safe = bool(curriculum.get('full_safe', song.get('completed') and not song.get('safety_invalidated')))
        self.safe_full += full_safe
        self.successes += bool(song.get('stage_success'))
        targets, left = song.get('target_count', 0), song.get('left_success_count', 0)
        self.note_targets += targets
        self.note_left += left
        if full_safe:
            self.full_targets += targets
            self.full_left += left
        self.reasons.update(row.get('failure_reasons', []))
        for field in ('reward', 'cost', 'steps', 'task_time_s'):
            self.add_value('episode_'+field, row.get(field))
        for field in ('reach_fraction', 'contact_fraction'):
            self.add_value('episode_'+field, curriculum.get(field))
            if full_safe:
                self.add_value('full_safe_episode_'+field, curriculum.get(field))
        self.add_value('episode_clean_audible_fraction', song.get('mean_clean_audible_fraction'))

    def merge(self, other):
        for name in ('updates','transitions','episodes','steps','timeline','failures','successes','safe_full',
                     'note_targets','note_left','full_targets','full_left','retry_count','updates_with_retries'):
            setattr(self,name,getattr(self,name)+getattr(other,name))
        self.reasons.update(other.reasons)
        self.stages.update(other.stages)
        self.first_update = other.first_update if self.first_update is None else min(self.first_update,other.first_update)
        self.last_update = other.last_update if self.last_update is None else max(self.last_update,other.last_update)
        for name, mean in other.means.items():
            self.means.setdefault(name,Mean()).merge(mean)

    def result(self):
        ratio = lambda a, b: a/b if b else None
        return dict(update_index_first=self.first_update, update_index_last=self.last_update,
            updates=self.updates, committed_transitions=self.transitions, ended_episodes=self.episodes,
            timeline_complete=self.timeline, physical_failure=self.failures, full_safe=self.safe_full,
            stage_success=self.successes, timeline_complete_fraction=ratio(self.timeline, self.episodes),
            physical_failure_fraction=ratio(self.failures, self.episodes),
            full_safe_fraction=ratio(self.safe_full, self.episodes),
            stage_success_fraction_all_ended=ratio(self.successes, self.episodes),
            stage_success_fraction_full_safe=ratio(self.successes, self.safe_full),
            left_notes_all_ended=dict(achieved=self.note_left, targets=self.note_targets,
                fraction=ratio(self.note_left, self.note_targets)),
            left_notes_full_safe=dict(achieved=self.full_left, targets=self.full_targets,
                fraction=ratio(self.full_left, self.full_targets)),
            failure_reasons=dict(self.reasons), curriculum_stage_update_counts=dict(self.stages),
            kl_retries=self.retry_count, updates_with_kl_retries=self.updates_with_retries,
            means={name: value.result() for name, value in self.means.items()})


def analyze(run, width):
    audit = Counter()
    groups = {name: Group() for name in ('overall', 'first', 'last')}
    seen, first_rows, last_rows, bins = set(), {}, {}, {}
    latest = {}
    def consume(row):
        nonlocal latest
        index = row['update_index']
        if index in seen:
            return
        if row.get('journal', {}).get('committed', 0) < row['transitions']:
            raise ValueError('Update without committed transition evidence: '+str(index))
        seen.add(index)
        summary = Group()
        summary.update(row)
        groups['overall'].merge(summary)
        bins.setdefault(index//width,Group()).merge(summary)
        first_rows[index] = last_rows[index] = summary
        if len(first_rows) > width:
            del first_rows[max(first_rows)]
        if len(last_rows) > width:
            del last_rows[min(last_rows)]
        if not latest or index > latest['update_index']:
            latest = dict(update_index=index,optimizer_updates=row.get('optimizer_updates'),
                journal=row.get('journal'),physics_steps=row.get('physics_steps'))
    for row in lines(run/'learning_metrics.jsonl', audit):
        consume(row)
    # A complete update file can precede its append-log newline. Keep only
    # bounded numeric summaries, never all episode dictionaries in memory.
    for path in sorted(run.glob('update_*.json')):
        index = int(path.stem.split('_')[-1])
        if index not in seen:
            row = json_document(path)
            if row is None:
                audit['incomplete_update_files_skipped'] += 1
            else:
                consume(row)
    for index in sorted(first_rows):
        groups['first'].merge(first_rows[index])
    for index in sorted(last_rows):
        groups['last'].merge(last_rows[index])
    ordered, committed_ids = sorted(seen), seen
    episode_audit = Counter()
    pending_reasons = Counter()
    for row in lines(run/'episodes.jsonl', audit):
        committed = row['update_index'] in committed_ids
        episode_audit['logged_episode_rows'] += 1
        episode_audit['rows_from_committed_updates' if committed else 'rows_without_committed_update_snapshot'] += 1
        if not committed:
            pending_reasons.update(row['episode'].get('failure_reasons', []))
    report = json_document(run/'report.json')
    settings = json_document(run/'settings.json') or {}
    journal = report.get('journal') if report else latest.get('journal')
    observed_episodes = groups['overall'].episodes
    return dict(schema='guitar_learning.learning_analysis.v1', generated_at_utc=datetime.now(timezone.utc).isoformat(),
        run=str(run.resolve()), run_finalized=report is not None, run_completed=report.get('completed') if report else None,
        failure=report.get('failure') if report else None, requested_updates=settings.get('updates'),
        final_report_committed_transitions=report.get('transitions') if report else None,
        final_metrics_snapshot_matches_report=(report.get('transitions') == groups['overall'].transitions and
            len(report.get('updates', [])) == groups['overall'].updates) if report else None,
        settings={k: settings.get(k) for k in ('num_envs', 'horizon', 'size', 'initial_std', 'physics_backend')},
        snapshot_last_update_index=ordered[-1] if ordered else None,
        latest_physics_steps=latest.get('physics_steps'), journal=journal,
        journal_scope='Final report if present; otherwise latest committed update. Active collection after that snapshot is not estimated.',
        episode_audit=dict(episode_audit, committed_update_episode_count=observed_episodes,
            noncommitted_failure_reasons=dict(pending_reasons)),
        read_audit=dict(audit), overall=groups['overall'].result(),
        first_window=groups['first'].result(), last_window=groups['last'].result(), window_updates=width,
        windows=[dict(bin_start=k*width, bin_end_inclusive=(k+1)*width-1, **v.result()) for k,v in sorted(bins.items())],
        denominator_notes=[
            'Reward/cost means are weighted by committed rollout transitions, not episodes.',
            'Episode fractions use ended episodes in committed updates; ongoing songs are excluded, not failures or successes.',
            'Wrist reach/contact fractions divide achieved notes by all target notes in each episode, including unreached future notes of failed episodes.',
            'All-ended and full-safe-only note fractions are separate. A PPO horizon boundary is not a song boundary.',
            'Failure reasons overlap; their counts can exceed failed episodes.',
            'KL scalar is the last accepted optimizer attempt; minibatch means use actual sample visits. Critic MSE uses full-rollout diagnostics; EV is the arithmetic mean of per-update EV.',
            'First and last windows overlap before twice the window size; update bins can contain partial windows.',
            'GPU loaded-body geometric contact candidates and stage success do not establish real string pressure or acoustic success.',
            'Logged episodes without a committed update snapshot are excluded. The final journal distinguishes sampled/logged/durable/committed/discarded transitions.'
        ])


def markdown(value):
    def number(x):
        return '해당 없음' if x is None else format(x, '.6g')
    def mean(group, key):
        return number(group['means'].get(key, {}).get('mean'))
    overall = value['overall']
    text = ['# GPU 장기 학습 분석', '',
        '분석 시점: '+value['generated_at_utc'], '',
        '최종 실행 종료: '+str(value['run_finalized'])+' / 정상 완료: '+str(value['run_completed']), '',
        '최종 보고서와 분석 스냅샷의 전이·업데이트 일치: '+str(value['final_metrics_snapshot_matches_report']), '',
        'PPO 반영 업데이트 %d회, 전이 %d개, 종료 에피소드 %d개입니다.' %
        (overall['updates'], overall['committed_transitions'], overall['ended_episodes']), '',
        '진행 중인 곡은 완주·실패 분모에 넣지 않습니다. 접촉 수치는 GPU 기하 후보이며 음향 성공이 아닙니다.', '',
        '| 구간 | 업데이트 | 종료 에피소드 | 전곡 종료 | 물리 실패 | 단계 성공 | 평균 보상/전이 | 평균 비용/전이 | 손목 도달 | 접촉 후보 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name, group in [('전체', overall), ('처음', value['first_window']), ('마지막', value['last_window'])]+[
            ('%d–%d' % (row['bin_start'], row['bin_end_inclusive']), row) for row in value['windows']]:
        text.append('| %s | %d | %d | %d | %d | %d | %s | %s | %s | %s |' %
            (name, group['updates'], group['ended_episodes'], group['timeline_complete'], group['physical_failure'],
             group['stage_success'], mean(group,'mean_reward'), mean(group,'mean_cost'),
             mean(group,'episode_reach_fraction'), mean(group,'episode_contact_fraction')))
    text += ['', '커리큘럼 진행도: 처음 %s → 마지막 %s (최대 %s).' % tuple(number(overall['means'].get('curriculum_progress',{}).get(k)) for k in ('first','last','max')), '',
        '물리 실패 원인별 건수: '+json.dumps(overall['failure_reasons'],ensure_ascii=False)+'.', '',
        '| 구간 | KL | 보상 critic MSE | 비용 critic MSE | 보상 EV 평균 | 비용 EV 평균 | KL 재시도 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name, group in [('처음',value['first_window']),('마지막',value['last_window'])]+[
            ('%d–%d' % (r['bin_start'],r['bin_end_inclusive']),r) for r in value['windows']]:
        text.append('| %s | %s | %s | %s | %s | %s | %d |' % (name,mean(group,'analytic_kl'),
            mean(group,'reward_critic_mse'),mean(group,'cost_critic_mse'),
            mean(group,'reward_critic_explained_variance_mean_of_updates'),
            mean(group,'cost_critic_explained_variance_mean_of_updates'),group['kl_retries']))
    text += ['', '기록/반영 집계: `'+json.dumps(value['journal'],ensure_ascii=False)+'`', '',
        '에피소드 로그 대조: `'+json.dumps(value['episode_audit'],ensure_ascii=False)+'`', '',
        '진행 중 파일 읽기: `'+json.dumps(value['read_audit'],ensure_ascii=False)+'`', '', '분모와 해석:', '']
    text += ['- '+note for note in value['denominator_notes']]
    return '\n'.join(text)+'\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,default=Path(__file__).with_name('train1024_large_2000'))
    parser.add_argument('--out',type=Path,default=Path(__file__).parent)
    parser.add_argument('--window',type=int,default=100)
    args = parser.parse_args()
    if args.window < 1:
        parser.error('--window must be positive')
    result = analyze(args.run,args.window)
    args.out.mkdir(parents=True,exist_ok=True)
    for name, content in [('learning_analysis.json',json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n'),
                          ('learning_analysis.md',markdown(result))]:
        path = args.out/name
        temporary = path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(content)
        temporary.replace(path)
    print(json.dumps(dict(updates=result['overall']['updates'],episodes=result['overall']['ended_episodes'],finalized=result['run_finalized'])))


if __name__ == '__main__':
    main()
