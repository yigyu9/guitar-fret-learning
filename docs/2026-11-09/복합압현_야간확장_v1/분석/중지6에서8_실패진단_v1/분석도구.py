"""완료된 A0 원문을 읽어 탐색 중 접촉과 평균 정책의 차이를 정리한다."""
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/a0-diagnosis-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent
STUDY = OUT.parents[1]


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(pins):
    changed = [p for p, digest in pins.items() if sha(p) != digest]
    if changed:
        raise RuntimeError('원문 SHA 불일치: ' + ', '.join(changed))


def main():
    seal = STUDY / '검증/실행봉인.json'
    pins = read(seal)['pins']
    verify(pins)
    state_path = STUDY / '진행상황.json'
    state = read(state_path)
    sources = {str(state_path): sha(state_path), str(seal): sha(seal)}
    data = []
    for label in ('A0_arm005', 'A0_arm010', 'A0_arm015'):
        episodes = []
        stages = []
        for suffix in ('train100', 'extend100'):
            path = Path(state['tasks'][label + '_s7_' + suffix]['out']) / 'J/episodes.jsonl'
            sources[str(path)] = sha(path)
            group = [r['episode'] for r in rows(path)]
            episodes.extend(group)
            stages.append(dict(stage=suffix, episodes=len(group),
                               B_contact=sum(e['left_note_ledger']['values']['contact_time'][1] > 0 for e in group),
                               B_achieved=sum(e['left_note_ledger']['values']['left'][1] for e in group)))
        case = state['cases'][label + '_s7']
        evaluated = case['evaluations']['200']
        path = Path(evaluated['out']) / 'episodes.jsonl'
        sources[str(path)] = sha(path)
        policy = [r['episode'] for r in rows(path)]
        n = len(policy)
        terms = {k: sum(e['reward_components'][k] for e in policy) / n
                 for k in policy[0]['reward_components']}
        data.append(dict(label=label, arm_initial_std=case['arm_std'], training_episodes=len(episodes),
                         B_contact_episodes=sum(e['left_note_ledger']['values']['contact_time'][1] > 0 for e in episodes),
                         B_achieved_episodes=sum(e['left_note_ledger']['values']['left'][1] for e in episodes),
                         B_longest_clean_s=max(e['left_note_ledger']['values']['best_clean_streak'][1] for e in episodes),
                         stages=stages, mean_policy=evaluated['result'], mean_policy_reward_terms=terms))
    native_task = next(item for key, item in state['tasks'].items() if key.startswith('A0_native_'))
    native_out = Path(native_task['out'])
    for filename in ('report.json', 'episode.json', 'diagnostics.json'):
        path = native_out / filename
        sources[str(path)] = sha(path)
    native_report = read(native_out / 'report.json')
    native_episode = read(native_out / 'episode.json')
    native = dict(out=str(native_out), task_success=native_report['task_success'],
                  requested_path_rate_feasible=native_report['requested_path_rate_feasible'],
                  clean_seconds=native_episode['left_note_ledger']['values']['clean'],
                  timing=read(native_out / 'diagnostics.json')['summary'],
                  undiscounted_logged_reward=native_episode['reward'],
                  reward_terms=native_episode['reward_components'])
    payload = dict(completed=True, source_sha256=sources, global_seal_verified_files=len(pins), cases=data,
                   native_reference=native,
                   scope='동일 seed7·200회·896회 안팎 에피소드의 조건부 비교. 접촉은 contact_time>0, 달성은 left 플래그. 평균 정책은 같은 준비 입력의16환경이며 독립 학습16시드가 아님.')
    (OUT / '핵심수치.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    labels = ['0.050', '0.100', '0.150']
    x = list(range(3))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5), layout='constrained')
    ax[0].bar([i - .2 for i in x], [100 * d['B_contact_episodes'] / d['training_episodes'] for d in data], width=.2, label='Sampled: any B contact')
    ax[0].bar(x, [100 * d['B_achieved_episodes'] / d['training_episodes'] for d in data], width=.2, label='Sampled: B achieved')
    ax[0].bar([i + .2 for i in x], [100 * d['mean_policy']['clean_fraction_by_target'][1] for d in data], width=.2, label='Mean policy: B clean fraction')
    ax[0].set(xticks=x, xticklabels=labels, xlabel='Initial arm latent std (finger initial std 0.35)', ylabel='Percent', title='B target (S3 F8): exploration vs mean policy', ylim=(0, 36))
    ax[0].legend(fontsize=8)
    ax[1].bar(x, [d['B_longest_clean_s'] for d in data], color='#279879')
    ax[1].axhline(1.5, linestyle='--', color='#a23b3b', label='Full note length: 1.5 s')
    ax[1].set(xticks=x, xticklabels=labels, xlabel='Initial arm latent std', ylabel='Seconds', title='Longest B clean streak found during training', ylim=(0, 1.7))
    ax[1].legend(fontsize=8)
    for axes in ax:
        axes.grid(axis='y', alpha=.2)
    fig.savefig(OUT / '탐색과평균정책_비교.png', dpi=160)
    plt.close(fig)
    verify(pins)
    verify(sources)
    print(json.dumps([dict(std=d['arm_initial_std'], B_contact=d['B_contact_episodes'],
                           B_achieved=d['B_achieved_episodes'], total=d['training_episodes'],
                           longest=d['B_longest_clean_s']) for d in data]))


if __name__ == '__main__':
    main()
