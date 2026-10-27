"""Read a provisional gzip prefix without claiming committed or complete data."""
import gzip
import json
from pathlib import Path

PHASE = Path(__file__).resolve().parent


def main():
    result = {}
    for hand in ('left', 'right'):
        folder = PHASE/(hand+'_run_v1')
        status = json.loads((folder/'status.json').read_text())
        updates = sorted(folder.glob('update_*.json'))
        episodes = successes = failures = candidates = count = 0
        guides = []; distances = []; reward = cost = 0.
        last = None; incomplete = False
        try:
            with gzip.open(folder/'transitions.jsonl.gz', 'rt') as stream:
                for line in stream:
                    row = json.loads(line)
                    for info, r in zip(row['infos'], row['reward']):
                        count += 1; reward += r; cost += info['cost']; last = info
                        candidates += int(any(info['fret_candidates'].values()))
                        distances.extend(info['goal_distance_m'].values())
                        guide = info.get('pick_guide')
                        if guide and guide['sweep_active']: guides.append(guide['distance_m'])
                        if 'episode' in info:
                            episodes += 1
                            successes += int(info['episode']['specialist']['stage_success'])
                            failures += int(info['episode']['reason'] == 'terminal_failure')
        except (EOFError, json.JSONDecodeError):
            incomplete = True
        item = dict(provisional_prefix=True, open_gzip_tail=incomplete,
            phase=status['phase'], elapsed_s=round(status['elapsed_s'], 1),
            update_count=len(updates), committed_transitions=len(updates)*512,
            parsed_transitions=count, complete_episodes=episodes, stage_success=successes,
            physical_failures=failures, endpoint_contact_candidate_samples=candidates,
            memory_available_gib=round(status['available_memory_bytes']/2**30, 2))
        if count: item.update(mean_reward_per_tick=reward/count, mean_cost_per_tick=cost/count,
                             mean_goal_marker_mm=1000*sum(distances)/len(distances))
        if guides: item['mean_sweep_guide_mm']=1000*sum(guides)/len(guides)
        if last: item['last_specialist']=last['specialist']
        result[hand] = item
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
