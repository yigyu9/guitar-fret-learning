"""Compare ended, committed episodes by curriculum and repeated whole songs."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

FIELDS = ('reach', 'contact', 'progress', 'steps', 'reward', 'cost', 'notes')


def complete_lines(path):
    if path.exists():
        with path.open() as stream:
            for line in stream:
                if not line.endswith('\n'):
                    break
                if line.strip():
                    yield json.loads(line)


class Summary:
    def __init__(self):
        self.count = 0
        self.total = Counter()
        self.first = self.last = None

    def add(self, value, update):
        self.count += 1
        self.total.update(value)
        self.first = update if self.first is None else min(update, self.first)
        self.last = update if self.last is None else max(update, self.last)

    def result(self):
        return dict(episodes=self.count, update_first=self.first, update_last=self.last,
                    mean={k: v/self.count for k, v in self.total.items()} if self.count else {})


def analyze(run, last_update):
    committed, changes = set(), []
    previous = None
    for row in complete_lines(run/'learning_metrics.jsonl'):
        index = row['update_index']
        if last_update is not None and index > last_update:
            continue
        committed.add(index)
        progress = row.get('left_curriculum', {}).get('progress')
        if progress != previous:
            changes.append(dict(update_index=index, progress=progress))
            previous = progress
    groups = defaultdict(Summary)
    pairs = defaultdict(Summary)
    ordinal, safe_ordinal = Counter(), Counter()
    first_safe = {}
    logged = excluded = 0
    for row in complete_lines(run/'episodes.jsonl'):
        logged += 1
        update = row['update_index']
        if update not in committed:
            excluded += 1
            continue
        episode = row['episode']
        env = episode['env_id']
        curriculum, song = episode['left_curriculum'], episode['song']
        safe = episode['reason'] == 'timeline_complete' and curriculum['full_safe']
        kind = 'full_safe' if safe else 'failure_or_other_end'
        value = dict(reach=curriculum['reach_fraction'], contact=curriculum['contact_fraction'],
            progress=curriculum['progress'], steps=episode['steps'], reward=episode['reward'],
            cost=episode['cost'], notes=song['left_success_count'])
        ordinal[env] += 1
        for key in ('all/'+kind, 'updates_%04d_%04d/' % (update//100*100,update//100*100+99)+kind,
                    'progress_%.1f/' % value['progress']+kind,
                    'ended_episode_%02d/' % ordinal[env]+kind):
            groups[key].add(value, update)
        if safe:
            safe_ordinal[env] += 1
            n = safe_ordinal[env]
            groups['safe_song_%02d' % n].add(value, update)
            if n == 1:
                first_safe[env] = value
            else:
                base = first_safe[env]
                paired = {label+'.'+field: source[field] for label,source in
                          (('first',base),('later',value)) for field in FIELDS}
                paired.update({'delta.'+field: value[field]-base[field] for field in FIELDS})
                pairs[n].add(paired, update)
    return dict(schema='guitar_learning.learning_cohorts.v1',
        generated_at_utc=datetime.now(timezone.utc).isoformat(), run=str(run.resolve()),
        snapshot_last_update_index=max(committed) if committed else None,
        committed_updates=len(committed), logged_episode_rows=logged,
        excluded_episode_rows_without_committed_update_in_snapshot=excluded,
        curriculum_progress_changes=changes, groups={k:v.result() for k,v in sorted(groups.items())},
        paired_first_vs_later_safe_song={str(k):v.result() for k,v in sorted(pairs.items())},
        limitations=[
            'Only complete JSONL lines from committed update snapshots enter the episode cohorts.',
            'Full-safe songs always contain all1969 control ticks and all67 target notes; failed songs stop early and have unreached future notes in their fixed67-note denominator.',
            'Safe-song ordinal counts complete safe songs per environment; ended-episode ordinal also counts failures/reset attempts.',
            'Paired comparisons use exactly the same environments in each pair, but do not freeze policy or curriculum; they are not controlled evaluations.',
            'Episode progress is the progress at episode end. Global curriculum can change during a song; it is not a constant episode treatment.',
            'Contact is a GPU loaded-geometry candidate, not calibrated string pressure or acoustic success.',
            'Raw episode reward is not comparable across changed curriculum weights, and a lower mixed-cohort mean alone does not prove worse policy.'
        ])


def markdown(value):
    lines = ['# 완주·실패 에피소드와 학습 단계 비교', '',
        'Committed snapshot last update: '+str(value['snapshot_last_update_index']), '',
        '| Cohort | Episodes | Updates | Wrist reach | Contact candidate | End progress | Achieved notes/67 |',
        '|---|---:|---|---:|---:|---:|---:|']
    for name, group in value['groups'].items():
        m=group['mean']
        lines.append('| %s | %d | %s–%s | %.6f | %.6f | %.3f | %.3f |' %
            (name,group['episodes'],group['update_first'],group['update_last'],m['reach'],m['contact'],m['progress'],m['notes']))
    lines += ['', '| Same environments: first vs later safe song | Pairs | Reach first→later | Contact first→later | Progress first→later |',
        '|---|---:|---|---|---|']
    for n, group in value['paired_first_vs_later_safe_song'].items():
        m=group['mean']
        lines.append('| 1→%s | %d | %.6f→%.6f | %.6f→%.6f | %.3f→%.3f |' %
            (n,group['episodes'],m['first.reach'],m['later.reach'],m['first.contact'],m['later.contact'],m['first.progress'],m['later.progress']))
    lines += ['', 'Interpretation limits:', '']+['- '+x for x in value['limitations']]
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,default=Path(__file__).with_name('train1024_large_2000'))
    parser.add_argument('--last-update',type=int)
    parser.add_argument('--out',type=Path,default=Path(__file__).parent)
    args=parser.parse_args()
    result=analyze(args.run,args.last_update)
    args.out.mkdir(parents=True,exist_ok=True)
    for name,content in [('cohort_analysis.json',json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n'),
                         ('cohort_analysis.md',markdown(result))]:
        path=args.out/name
        temporary=path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(content)
        temporary.replace(path)
    print(json.dumps(dict(last_update=result['snapshot_last_update_index'],groups=len(result['groups']))))


if __name__=='__main__':
    main()
