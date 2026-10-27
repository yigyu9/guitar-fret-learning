"""Reconstruct clock coverage from a completed, failure-free synchronized run."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


OUT = Path(__file__).resolve().parents[1]
RUN = OUT.parents[1]/'03_short_learning/pilot_incremental_seed7_v2_retry2/train'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    paths = [Path(__file__), *[RUN/name for name in ('settings.json', 'metrics.jsonl', 'episodes.jsonl')]]
    before = {str(p): digest(p) for p in paths}
    settings = json.loads((RUN/'settings.json').read_text())
    view = settings['song']['short_learning']['view']
    horizon, count, updates = settings['horizon'], settings['num_envs'], settings['updates']
    length = view['duration_ticks']
    completed = Counter()
    with (RUN/'episodes.jsonl').open() as f:
        for line in f:
            row = json.loads(line)
            env_id = row['env_id']; completed[env_id] += 1
            assert row['steps'] == length and row['reason'] == 'timeline_complete'
            assert not row['termination']['physical_failure'] and not row['termination']['wrist_failure']
            assert row['update'] == math.ceil(completed[env_id]*length/horizon)
    assert len(completed) == count and set(completed.values()) == {updates*horizon//length}
    with (RUN/'metrics.jsonl').open() as f:
        metrics = [json.loads(line) for line in f]
    assert len(metrics) == updates
    rows = []
    for update in range(1, updates+1):
        local = np.arange((update-1)*horizon, update*horizon) % length
        before_s, after_s = local/60., (local+1)/60.
        overlap = np.maximum(0, np.minimum(after_s, view['local_end_s'])-
                             np.maximum(before_s, view['local_onset_s']))
        rows.append(dict(update=update, start_local_tick=int(local[0]),
            audible_overlap_ticks=int((overlap > 1e-12).sum()),
            audible_overlap_s=float(overlap.sum())))
    music_updates = sum(row['audible_overlap_ticks'] > 0 for row in rows)
    with (OUT/'update_coverage.csv').open('w') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    assert before == {str(p): digest(p) for p in paths}
    result = dict(scope='Source score audible-window coverage, not sound, contact, received positive reward, or gradient attribution',
        horizon=horizon, num_envs=count, updates=updates, episode_ticks=length,
        source_time_hz=60, view=view, per_env_completed=dict(completed),
        all_recorded_episode_end_updates_match_synchronized_clock=True,
        phase_period_updates=length//math.gcd(length, horizon),
        updates_with_audible_window=music_updates, updates_without_audible_window=updates-music_updates,
        fraction_updates_with_audible_window=music_updates/updates,
        audible_overlap_per_env_s=sum(row['audible_overlap_s'] for row in rows),
        raw_time_per_env_s=updates*horizon/60.,
        audible_time_fraction=sum(row['audible_overlap_s'] for row in rows)/(updates*horizon/60.),
        inputs_unchanged=True, input_sha256=before)
    (OUT/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'Noto Sans CJK JP', 'axes.unicode_minus':False})
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    axes[0].scatter([r['update'] for r in rows], [r['start_local_tick']/60 for r in rows], s=9)
    axes[0].axhspan(view['local_onset_s'], view['local_end_s'], color='#48a67d', alpha=.25,
                   label='원곡상 audible 시간창')
    axes[0].set_ylabel('수집 시작의 에피소드 시각(초)'); axes[0].legend(loc='upper right')
    axes[1].bar([r['update'] for r in rows], [r['audible_overlap_ticks'] for r in rows], color='#3988b9')
    axes[1].set_ylabel('음 시간창과 겹친 tick / 32'); axes[1].set_xlabel('PPO 업데이트')
    for ax in axes: ax.grid(alpha=.2); ax.set_axisbelow(True)
    fig.suptitle(f'중지 1음 진단: {updates}개 수집창 중 {music_updates}개에만 원곡 음 시간창 포함\n128환경의 실제 종료 원장으로 동기 시계를 검산 · 미래 보상을 못 본다는 뜻은 아님')
    fig.tight_layout(); fig.savefig(OUT/'coverage.png', dpi=150); plt.close(fig)
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','per_env_completed','view')}, indent=2))


if __name__ == '__main__':
    main()
