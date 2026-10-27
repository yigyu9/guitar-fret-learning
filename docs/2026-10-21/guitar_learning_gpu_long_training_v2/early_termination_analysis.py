"""Read-only evidence for the early-termination incentive hypothesis."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean


def complete_lines(path):
    if path.exists():
        with path.open() as stream:
            for line in stream:
                if not line.endswith('\n'):
                    break
                if line.strip():
                    yield json.loads(line)


def distribution(values):
    values = sorted(values)
    if not values:
        return dict(count=0)
    def percentile(q):
        x = (len(values)-1)*q
        i = int(x)
        return values[i]+(values[min(i+1,len(values)-1)]-values[i])*(x-i)
    return dict(count=len(values), mean=mean(values), minimum=values[0], p25=percentile(.25),
                median=percentile(.5), p75=percentile(.75), p90=percentile(.9), p95=percentile(.95),
                p99=percentile(.99), maximum=values[-1])


def summary(rows):
    return dict(episodes=len(rows), full_safe=sum(r['safe'] for r in rows),
        failed=sum(not r['safe'] for r in rows),
        distributions={field:distribution([r[field] for r in rows]) for field in
            ('duration_s','reward','cost','R_minus_cost_undiscounted_proxy','ordinal')})


def analyze(run, start, last):
    committed = set()
    cost_weights = []
    for row in complete_lines(run/'learning_metrics.jsonl'):
        if row['update_index'] <= last:
            committed.add(row['update_index'])
            if row['update_index'] >= start:
                cost_weights.append(row['cost_weight'])
    settings = json.loads((run/'settings.json').read_text())
    groups = defaultdict(list)
    ordinals, reasons = Counter(), Counter()
    first_safe, first_failure, last_failure = {}, {}, {}
    excluded = 0
    for row in complete_lines(run/'episodes.jsonl'):
        u = row['update_index']
        if u not in committed:
            excluded += 1
            continue
        e = row['episode']
        env = e['env_id']
        ordinals[env] += 1
        value = dict(env=env, update=u, ordinal=ordinals[env], duration_s=e['steps']/60.,
            reward=e['reward'], cost=e['cost'], cost_per_second=e['cost']/(e['steps']/60.),
            R_minus_cost_undiscounted_proxy=e['reward']-e['cost'],
            safe=e['reason']=='timeline_complete' and e['left_curriculum']['full_safe'])
        if value['safe']:
            first_safe.setdefault(env,value)
        if not start <= u <= last:
            continue
        kind = 'full_safe' if value['safe'] else 'failure'
        for name in ('all',kind,'updates_%d_%d' % (u//25*25,u//25*25+24),
                     'ended_cycle_%03d' % value['ordinal']):
            groups[name].append(value)
        if not value['safe']:
            reasons.update(e['failure_reasons'])
            duration = value['duration_s']
            groups['failure_'+('up_to_1s' if duration<=1 else '1_to_5s' if duration<=5 else 'over_5s')].append(value)
            first_failure.setdefault(env,value)
            last_failure[env] = value
    paired = {}
    for name, later in [('first_failure_in_window',first_failure),('last_failure_in_window',last_failure)]:
        ids = set(first_safe)&set(later)
        paired[name] = dict(environments=len(ids),
            first_safe=summary([first_safe[i] for i in ids]), failure=summary([later[i] for i in ids]),
            change_distributions={key:distribution([later[i][key]-first_safe[i][key] for i in ids])
                for key in ('duration_s','reward','cost','R_minus_cost_undiscounted_proxy')})
    all_rows = groups['all']
    return dict(schema='guitar_learning.early_termination_analysis.v1',
        generated_at_utc=datetime.now(timezone.utc).isoformat(), run=str(run.resolve()),
        requested_update_window=[start,last], snapshot_last_committed_update=max(committed) if committed else None,
        excluded_episode_rows_outside_committed_snapshot=excluded,
        ended_episodes_in_window=len(all_rows), failure_reasons=dict(reasons),
        ppo=settings['ppo'], cost_weight_observed=distribution(cost_weights),
        calibration_cost_rate_per_second=dict(
            window_full_safe=distribution([r['cost_per_second'] for r in groups['full_safe']]),
            first_full_safe_per_environment=distribution([r['cost_per_second'] for r in first_safe.values()]),
            definition='Completed full-safe episode total cost / duration_s; units cost per second, not per control tick',
            scope='Observed policy/state cost density; not an estimate of unavoidable or counterfactual remaining cost'),
        groups={k:summary(v) for k,v in sorted(groups.items())}, paired_same_environment=paired,
        source_semantics=[
            'Failure terminates the current song; the collector zeros terminal bootstrap and resets that environment. Future song rewards and costs do not occur in that episode.',
            'Failure adds reward -2 and cost +5 to the failure tick, with positive reward suppressed; accumulated cost before failure remains charged.',
            'Actual PPO combines reward and cost advantages, using reward gamma .99, cost gamma1 and GAE lambda .95. R-C totals below are descriptive undiscounted proxies, not exact actor advantages or gradients.',
            'With fixed cost weight1 and episodic undiscounted cost, avoiding future large song cost by ending an episode is a real design risk; repeated resets can simultaneously worsen cost per transition.',
            'Full-safe and failed records come from different policies/times/visited states. Even same-environment comparisons do not establish a counterfactual continuation cost or prove the cause of a policy gradient.',
            'A shrinking failed episode duration and smaller total episode cost support the risk hypothesis; they do not identify whether the behavior is learned escape, loss of control, critic error, or another training effect.',
            'Cycle ordinal counts all ended episodes per environment, including failures. Ongoing episodes are excluded from the completed-episode distributions.',
            'No native failure claim, new penalty, or implementation change is inferred from increased policy failures.'
        ])


def markdown(value):
    rows = ['# 조기 종료 유인 위험 분석', '', '업데이트 구간: '+str(value['requested_update_window']), '',
        '종료 에피소드 %d개, 마지막 반영 업데이트 %s.' % (value['ended_episodes_in_window'],value['snapshot_last_committed_update']), '',
        '조기 종료는 남은 곡의 비용도 끝냅니다. 아래 총보상·총비용 분포는 이 설계 위험을 조사하는 관측 자료이며, 정책이 의도적으로 실패하도록 학습했다는 증거는 아닙니다.', '',
        '| 구분 | 종료 수 | 평균 길이(s) | 길이 중앙값(s) | 평균 총보상 | 평균 총비용 | 평균 미할인 R-C 참고값 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for key,group in value['groups'].items():
        if not group['episodes']:
            continue
        d=group['distributions']
        rows.append('| %s | %d | %.4f | %.4f | %.4f | %.4f | %.4f |' % (key,group['episodes'],
            d['duration_s']['mean'],d['duration_s']['median'],d['reward']['mean'],d['cost']['mean'],d['R_minus_cost_undiscounted_proxy']['mean']))
    rows += ['', '실패 원인별 건수(중복 가능): '+json.dumps(value['failure_reasons']), '',
        '| 동일 환경 비교 | 환경 수 | 첫 안전 전곡 길이→실패 길이(s) | 첫 안전 전곡 비용→실패 비용 |',
        '|---|---:|---|---|']
    for name,pair in value['paired_same_environment'].items():
        if not pair['environments']:
            continue
        a,b=pair['first_safe']['distributions'],pair['failure']['distributions']
        rows.append('| %s | %d | %.4f→%.4f | %.4f→%.4f |' % (name,pair['environments'],
            a['duration_s']['mean'],b['duration_s']['mean'],a['cost']['mean'],b['cost']['mean']))
    rows += ['', '비용 밀도 보정용 관측 분포(cost/s): `'+json.dumps(value['calibration_cost_rate_per_second'],ensure_ascii=False)+'`', '', '원래 첫 안전 전곡과 최근 실패를 비교하면 좋은 완주 정책이 항상 실패보다 불리한 것은 아닙니다. 현재의 고비용 궤적을 일찍 끝내 손실을 줄일 가능성과, 좋은 완주 정책의 가치가 더 높다는 사실은 함께 성립할 수 있습니다.', '', '해석의 한계와 코드 경로:', '']+['- '+text for text in value['source_semantics']]
    return '\n'.join(rows)+'\n'


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,default=Path(__file__).with_name('train1024_large_2000'))
    parser.add_argument('--start-update',type=int,default=400)
    parser.add_argument('--last-update',type=int,default=499)
    parser.add_argument('--out',type=Path,default=Path(__file__).parent)
    args=parser.parse_args()
    if args.start_update<0 or args.last_update<args.start_update:
        parser.error('nonnegative ordered update window required')
    value=analyze(args.run,args.start_update,args.last_update)
    args.out.mkdir(parents=True,exist_ok=True)
    for name,content in [('early_termination_analysis.json',json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n'),
                         ('early_termination_analysis.md',markdown(value))]:
        path=args.out/name
        temporary=path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(content)
        temporary.replace(path)
    print(json.dumps(dict(episodes=value['ended_episodes_in_window'],snapshot=value['snapshot_last_committed_update'])))


if __name__=='__main__':
    main()
