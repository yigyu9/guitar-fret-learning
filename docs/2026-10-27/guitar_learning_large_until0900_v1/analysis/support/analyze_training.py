"""Read-only, single-pass analysis of completed training episodes; no GPU imports."""
import collections
import json
from pathlib import Path
import time

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'run_01/J'
OUT = ROOT / 'analysis'
REWARDS = ['song_left_approach', 'song_left_contact', 'song_clean_hold',
           'song_left_success', 'song_wrong_press', 'song_performance_deficit',
           'song_finger_standby', 'song_thumb_support', 'action_change']
LABELS = ['목표 패드 접근', '최초 접촉', '압현 유지', '압현 달성', '오압현',
          '음 수행 부족', '대기 자세', '엄지 안내', '행동 변화']


class Aggregate:
    def __init__(self):
        self.n = 0
        self.s = collections.Counter()
        self.reasons = collections.Counter()
        self.reward = collections.Counter()
        self.cost = collections.Counter()
        self.times = collections.defaultdict(list)
        self.arrays = {}

    def array(self, key, value):
        value = np.asarray(value, dtype=float)
        if key not in self.arrays:
            self.arrays[key] = np.zeros_like(value)
        self.arrays[key] += value

    def add(self, e):
        self.n += 1
        song = e['song']
        self.s.update(dict(success=song['left_success_count'],
            target_count=song['denominator'], seconds=e['task_time_s'],
            clean_fraction=song['mean_clean_audible_fraction'],
            any_success=int(song['left_success_count'] > 0),
            stage_success=int(song['stage_success']), reward=e['reward'], cost=e['cost']))
        term = e['termination']
        self.reasons.update(['timeline_complete'] if e['reason'] == 'timeline_complete' else [])
        self.reasons.update(['physical_failure'] if term['physical_failure'] else [])
        self.reasons.update(['wrist_failure'] if term['wrist_failure'] else [])
        self.reasons.update(e['failure_reasons'])
        self.times['all'].append(e['task_time_s'])
        self.times[term['primary_reason']].append(e['task_time_s'])
        self.reward.update(e['reward_components'])
        self.cost.update(e['cost_components'])
        fingers = e['left_curriculum']['finger_metrics']
        for key in ['near_fraction', 'contact_fraction', 'success_fraction', 'clean_fraction']:
            self.array('finger_'+key+'_weighted', [f[key]*f['target_count'] for f in fingers])
        self.array('finger_targets', [f['target_count'] for f in fingers])
        ledger = e['left_note_ledger']
        mask = np.asarray(ledger['focus_mask'], dtype=bool)
        values = ledger['values']
        for key in ['left', 'near_done', 'contact_done', 'clean', 'wrong', 'missing',
                    'exposure_time', 'near_time', 'geometry_time', 'loaded_target_time',
                    'contact_time', 'contact_progress', 'best_contact_streak',
                    'best_clean_streak', 'body_load_time', 'other_higher_time',
                    'own_wrong_fret_time', 'own_wrong_string_time']:
            self.s['ledger_'+key] += float(np.asarray(values[key])[mask].sum())
        exposure = np.asarray(values['exposure_time'])
        exposed = mask & (exposure > 0)
        self.s['exposed_note_instances'] += int(exposed.sum())
        self.s['unexposed_note_instances'] += int((mask & ~exposed).sum())
        self.s['exposed_surface_distance_sum_m'] += float(np.asarray(values['surface_min'])[exposed].sum())
        for key in ['left', 'contact_done', 'near_done', 'wrong', 'clean']:
            self.array('per_note_'+key, np.asarray(values[key])*mask)
        self.array('audible_wrong_source_note_seconds',
            np.asarray(ledger['wrong_press_sources']['values']['wrong_source_time'])[mask].sum(axis=0))
        self.array('per_note_selected', mask)
        self.array('per_note_exposed', exposed)
        d = e['left_episode_diagnostics']
        self.s['physics_sampled_s'] += d['physics_sampled_s']
        t = d['thumb_support']
        for key in ['sampled_s', 'valid_s', 'near_geometry_s', 'contact_candidate_s',
                    'quality_integral', 'selected_deep_gap_s', 'selected_negative_gap_s']:
            self.s['thumb_'+key] += t[key]
        self.s['thumb_region_excess_integral_m_s'] += t['mean_region_excess_m']*t['valid_s']
        self.s['thumb_gap_integral_m_s'] += t['mean_signed_gap_m']*t['valid_s']
        st = d['standby']
        for key in ['eligible_s', 'gate_weighted_s', 'contact_excluded_s', 'proximity_excluded_s']:
            self.array('standby_'+key, st[key])
        self.array('standby_quality_integral', np.asarray(st['eligible_mean_quality'])*st['gate_weighted_s'])
        runs = st['actual_gate_runs']
        for key in ['count', 'total_s', 'in_band_s', 'long_count', 'long_total_s', 'long_in_band_s']:
            self.array('standby_runs_'+key, runs[key])
        for phase in ['all', 'idle', 'press']:
            for key, value in d['extreme_combinations'][phase].items():
                self.array('extreme_'+phase+'_'+key, value)
        for phase in ['idle_angles', 'press_angles']:
            a = d[phase]
            self.array(phase+'_valid_s', a['valid_weighted_s'])
            self.array(phase+'_integral_rad_s', np.asarray(a['mean_rad'])*a['valid_weighted_s'])
        motion = e['left_finger_motion']
        for key in ['actual_range_rad', 'target_range_rad', 'actual_native_limit_fraction',
                    'target_native_limit_fraction', 'tracking_error_rms_rad', 'action_mean_abs']:
            self.array('motion_episode_mean_'+key, motion['values'][key])
        fd = e['finger_skill_diagnostics']
        self.array('motion_path_m', fd['motion']['path_m'])
        self.array('motion_phase_s', fd['motion']['observed_s'])
        recovery = fd['source_recovery']['by_finger']
        for key in ['planned_windows', 'planned_s', 'observed_s', 'in_band_s', 'complete_windows', 'occupancy80_windows']:
            self.array('recovery_'+key, [f[key] for f in recovery])
        if term['wrist_failure']:
            w = e['wrist_termination']
            self.s['wrist_audible_targets'] += len(w['audible_target_indices'])
            self.s['wrist_audible_clean_targets'] += sum(w['audible_clean_candidate'])
            self.reasons['wrist_axis_'+str(w['dominant_axis'])] += 1

    def result(self):
        def ratio(a, b):
            return np.divide(a, b, out=np.zeros_like(np.asarray(a, dtype=float)), where=np.asarray(b) != 0).tolist()
        a = self.arrays
        result = dict(episodes=self.n, totals=dict(self.s), reasons=dict(self.reasons),
            mean_success_per_episode=self.s['success']/self.n,
            success_per_selected_note=self.s['success']/self.s['target_count'],
            mean_selected_notes=self.s['target_count']/self.n,
            mean_episode_s=self.s['seconds']/self.n,
            reward_mean_per_completed_episode={k:self.reward[k]/self.n for k in REWARDS},
            cost_mean_per_completed_episode={k:v/self.n for k,v in self.cost.items()},
            times={k:dict(count=len(v), mean=float(np.mean(v)), median=float(np.median(v)),
                           p10=float(np.quantile(v,.1)),p90=float(np.quantile(v,.9))) for k,v in self.times.items()},
            summed_arrays={k:v.tolist() for k,v in a.items()})
        result['finger_fractions'] = {key:ratio(a['finger_'+key+'_weighted'],a['finger_targets'])
            for key in ['near_fraction','contact_fraction','success_fraction','clean_fraction']}
        result['standby_quality'] = ratio(a['standby_quality_integral'],a['standby_gate_weighted_s'])
        result['standby_in_band_fraction'] = ratio(a['standby_runs_in_band_s'],a['standby_runs_total_s'])
        result['extreme_fraction'] = {phase:{key:ratio(a['extreme_'+phase+'_'+key],a['extreme_'+phase+'_valid_s'])
            for key in ['index_like_s','pinky_like_s','distal_excess_s','any_s']} for phase in ['all','idle','press']}
        result['thumb'] = {key:self.s['thumb_'+key]/self.s['thumb_sampled_s'] for key in
            ['near_geometry_s','contact_candidate_s','quality_integral']}
        result['thumb']['mean_region_excess_m'] = self.s['thumb_region_excess_integral_m_s']/self.s['thumb_valid_s']
        result['thumb']['mean_signed_gap_m'] = self.s['thumb_gap_integral_m_s']/self.s['thumb_valid_s']
        for phase in ['idle_angles','press_angles']:
            result[phase+'_mean_deg'] = (np.asarray(ratio(a[phase+'_integral_rad_s'],a[phase+'_valid_s']))*180/np.pi).tolist()
        result['motion_episode_means'] = {k[len('motion_episode_mean_'):]: (v/self.n).tolist()
            for k,v in a.items() if k.startswith('motion_episode_mean_')}
        return result


def main():
    begin = time.monotonic()
    metrics = [json.loads(line) for line in (RUN/'learning_metrics.jsonl').open()]
    bins = collections.defaultdict(Aggregate)
    episode_count = 0
    # Metadata need not be deep-restored: every aggregated numeric field and scope
    # is dynamic in canonical rows. Static source names are read once separately.
    with (RUN/'episodes.jsonl').open() as stream:
        for expected, line in enumerate(stream):
            if not line.endswith('\n'):
                raise ValueError('Incomplete episode line')
            row = json.loads(line)
            if row['episode_id'] != expected:
                raise ValueError('Nonsequential episode ID')
            e = row['episode']; update = row['update_index']+1
            scope = e['finger_skill']['scope']
            keys = ['all', scope, f'block_{((update-1)//100)*100+1:04d}_{scope}']
            if update <= 250: keys.append('early_0001_0250_'+scope)
            if 501 <= update <= 750: keys.append('late_phrase_0501_0750_'+scope)
            if 801 <= update <= 1000: keys.append('early_full_0801_1000_'+scope)
            if 1151 <= update <= 1250: keys.append('checkpoint_1250_window_'+scope)
            if 901 <= update <= 1000: keys.append('checkpoint_1000_window_'+scope)
            if 1379 <= update <= 1478: keys.append('final_1379_1478_'+scope)
            for key in keys: bins[key].add(e)
            episode_count += 1
            if episode_count % 5000 == 0: print('episodes',episode_count,'seconds',round(time.monotonic()-begin,1),flush=True)
    assert episode_count == sum(r['episode_summary']['count'] for r in metrics)
    total_t = sum(r['transitions'] for r in metrics)
    results = {k:v.result() for k,v in sorted(bins.items())}
    weighted_rewards = {k:sum(r['reward_component_means'][k]*r['transitions'] for r in metrics)/total_t for k in REWARDS}
    metric_windows = {}
    for label, lo, hi in [('all',1,len(metrics)),('early',1,250),('late_phrase',501,750),
            ('early_full',801,1000),('checkpoint1000',901,1000),('checkpoint1250',1151,1250),('final',1379,1478)]:
        rows = metrics[lo-1:hi]
        metric_windows[label] = dict(updates=[lo,hi], mean_reward=float(np.mean([r['mean_reward'] for r in rows])),
            mean_cost=float(np.mean([r['mean_cost'] for r in rows])),
            reward_advantage_std=float(np.mean([r['diagnostics']['advantages']['reward_raw']['std'] for r in rows])),
            cost_advantage_std=float(np.mean([r['diagnostics']['advantages']['cost_raw']['std'] for r in rows])),
            reward_components={k:float(np.mean([r['reward_component_means'][k] for r in rows])) for k in REWARDS},
            actor_kl_mean=float(np.mean([r['analytic_kl'] for r in rows])),
            latent_entropy_mean=float(np.mean([r['diagnostics']['post_update']['latent_gaussian_entropy']['mean'] for r in rows])))
    data = dict(schema='overnight_training_analysis.v1',
        definitions=dict(episode_scope='completed episodes, including failed episodes; no active episode imputation',
            windows='1-based PPO collection update index; stochastic policy evolving within each window',
            full_song_denominator=67, candidate_contact='loaded-body geometric proxy, not calibrated string pressure or sound',
            episode_rewards='undiscounted sums, completed episodes only',
            transition_rewards='all committed control transitions including unfinished episodes; weights already applied',
            finger_motion='60Hz per-episode means/ranges; not 240Hz extrema; initial settling included',
            thumb_proximity_warning='legacy rear distance is not strict target-region contact; use thumb_support',
            extrema='predefined diagnostic shape patterns, not a proof of all unnatural postures'),
        optimizer_updates=len(metrics),transitions=total_t,completed_episodes=episode_count,
        exposure=metrics[-1]['cumulative_exposure_transitions'],
        transition_reward_component_means=weighted_rewards,metric_windows=metric_windows,groups=results,
        source_episode_bytes=(RUN/'episodes.jsonl').stat().st_size,
        analysis_seconds=time.monotonic()-begin)
    metadata=json.loads((RUN/'episode_metadata.json').read_text())
    data['audible_wrong_source_body_names']=next(field['value'] for field in metadata['fields']
        if field['path']==['left_note_ledger','wrong_press_sources','body_names'])
    data['audible_wrong_source_causes']=['other_higher','own_wrong_fret','own_wrong_string']
    data['definitions']['audible_wrong_source']='summed source-tagged audible note-seconds; simultaneous bodies/causes/targets can overlap, do not add to union wrong duration'
    (OUT/'training_analysis.json').write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    rows = []
    for key in ['early_0001_0250_phrase','late_phrase_0501_0750_phrase','early_full_0801_1000_full_song',
                'checkpoint_1000_window_full_song','checkpoint_1250_window_full_song','final_1379_1478_full_song']:
        if key not in results: continue
        v=results[key];n=v['episodes'];r=v['reasons']
        rows.append(f"| {key} | {n} | {v['mean_success_per_episode']:.3f}/{v['mean_selected_notes']:.2f} | {100*v['success_per_selected_note']:.2f}% | {100*r.get('timeline_complete',0)/n:.2f}% | {100*r.get('physical_failure',0)/n:.2f}% | {100*r.get('wrist_failure',0)/n:.2f}% |")
    summary = ['# 장시간 학습 로그 분석','',
        f"1478회, {total_t:,}전이, 완료 에피소드 {episode_count:,}개. 종료된 에피소드를 실패까지 모두 포함한다. 반복 번호는 1부터 표시한다.",'',
        '| 구간·범위 | 완료 수 | 평균 달성/평균 선택 음 | 선택 음 대비 달성 | 정상 끝 | 물리 실패 | 손목 실패 |',
        '|---|---:|---:|---:|---:|---:|---:|']+rows+['',
        '전곡은 분모가 항상 67이다. 구간 학습은 선택 음 수가 서로 달라 평균 분모를 함께 표시했다. 학습 중 탐색을 포함한 결과이므로 고정 체크포인트 평가 결과와 구분한다.',
        '','## 항목별 실제 보상','', '| 보상항 | 전체 전이당 평균 |','|---|---:|']
    summary += [f'| {label} | {weighted_rewards[key]:.8f} |' for key,label in zip(REWARDS,LABELS)]
    final=results['final_1379_1478_full_song']
    summary += ['', '## 진단과 해석','',
        f"- 마지막100회 전곡의 달성은 평균 {final['mean_success_per_episode']:.3f}/67이다. 손목 종료는 드물어졌지만, 압현 성공 자체는 낮다.",
        f"- 마지막100회 엄지의 엄격 목표영역 contact candidate 시간 비율은 {100*final['thumb']['contact_candidate_s']:.2f}%, 평균 안내 품질은 {final['thumb']['quality_integral']:.3f}이다. 넥 후면 근접 거리만으로 지지 성공을 판단하지 않는다.",
        '- 관절 각도·극단 패턴·대기 진입·손가락별 원장·오압현 원인은 JSON groups에 저장했다. 시간 분모는 항목마다 valid/eligible/selected를 구별한다.',
        '- 전체 에피소드 누적 보상과 종료 비용의 규모 차이만으로 인과를 단정하지 않는다. metric_windows에 reward/cost advantage 표준편차를 함께 보존했다.',
        '- 초기 구간과 후기 전곡은 난이도·분모가 다르므로 직접 성능 증감으로 비교할 수 없다. 체크포인트 비교는 동일 전곡 평가가 필요하다.',
        '- 추세 그림의 전곡은801회부터 표시했다. 전환 직후751–800회는32.82초 전곡을 끝내기 전에 짧게 실패한 에피소드가 먼저 기록되는 관측 편향이 있어 대표 비교에서 제외했다.',
        '- 행동 변화·자세 로그는 실제 움직임/목표 명령의 구분과 표본 주기를 유지한다. 고정 초기 자세의 물리 정착도 동작량에 포함된다.',
        '- 조기 종료 뒤 관측하지 않은 음은 성공으로 세지 않는다. 종료 시점 이후의 접촉·오압현 시간을 임의로 채우지 않는다.',
        '- 본 분석은 원자료를 한 번 순차 읽어 집계했으며 원자료·정책·환경 구현을 변경하지 않았다.','']
    (OUT/'training_summary.md').write_text('\n'.join(summary))
    supplement_final_diagnostics(data)
    plot(metrics,results)
    print('completed',episode_count,'seconds',round(time.monotonic()-begin,1),flush=True)


def supplement_final_diagnostics(data):
    f=data['groups']['final_1379_1478_full_song']; a=f['summed_arrays']
    n=f['episodes']; t=f['totals']; names=['검지','중지','약지','소지']
    rows=['','## 마지막100회 전곡 상세: 1379–1478회','',
        '아래는 전곡 완료 에피소드1868개(실패 포함)에 한정한 집계다. 고정 정책 평가가 아니다.','',
        '| 손가락 | 선택 목표 수 | 접촉 달성 수 | 압현 달성 수 | B gate>0 시간(초) | 그 시간 중 B 허용 각도대역 점유 |',
        '|---|---:|---:|---:|---:|---:|']
    for i,name in enumerate(names):
        rows.append(f"| {name} | {a['finger_targets'][i]:.0f} | {a['finger_contact_fraction_weighted'][i]:.0f} | {a['finger_success_fraction_weighted'][i]:.0f} | {a['standby_runs_total_s'][i]:.2f} | {100*f['standby_in_band_fraction'][i]:.2f}% |")
    rows += ['',
        '- B gate>0는 악보 기준 본인 press..end와 준비·해제 시간 보호, 관련 거리의 유한성에 따라 권고 보상이 활성화된 시간이다. 점유0%는 gate가 없다는 뜻이 아니라, 활성 시간에 권고 각도대역을 충족하지 못했다는 뜻이다. 초기 준비도 포함한다. 현행v5는 잔여 접촉 후보·근접 거리만으로 회복gate를 차단하지 않는다.',
        f"- 정적 source recovery 창은 별도 진단이다. 완전히 관측한 창은 {sum(a['recovery_complete_windows']):.0f}개이며, 전체 계획 창 {sum(a['recovery_planned_windows']):.0f}개 중 80%대역점유 달성은 {sum(a['recovery_occupancy80_windows']):.0f}개다. 미관측·부분관측 창을 완전관측으로 바꾸지 않았다.",
        f"- 엄지 엄격 목표영역 후보는 {t['thumb_contact_candidate_s']:.4f}/{t['thumb_sampled_s']:.1f}초({100*f['thumb']['contact_candidate_s']:.4f}%). 평균 품질 {f['thumb']['quality_integral']:.5f}, 평균 목표영역 초과 {1000*f['thumb']['mean_region_excess_m']:.2f}mm, 평균 signed gap {1000*f['thumb']['mean_signed_gap_m']:.2f}mm다. 로드된 기하 후보이며 실제 기타 줄 압력·소리는 인증하지 않는다.",
        f"- 소지 DIP−PIP>50° 패턴은 유효240Hz 표본시간 대비 전체 {100*f['extreme_fraction']['all']['distal_excess_s'][3]:.2f}%, 본인 press..end 구간 {100*f['extreme_fraction']['press']['distal_excess_s'][3]:.2f}%, 그 밖의 idle 구간 {100*f['extreme_fraction']['idle']['distal_excess_s'][3]:.2f}%다. idle 구분은 B gate와 별개다.",
        f"- 약지 DIP actual native 한계 점유는 각 에피소드의60Hz 끝점 비율을 단순평균해 {100*f['motion_episode_means']['actual_native_limit_fraction'][16]:.2f}%, 소지 MCP는 {100*f['motion_episode_means']['actual_native_limit_fraction'][17]:.2f}%다. 이는 모든 시간표본을 합친 비율이 아니며, 한계1e-6rad 판정·60Hz 표본의 제한을 가진다.",
        '- 극단 패턴은 사전에 정한 세 각도조합(MCP<−20°·PIP/DIP>60°, MCP/PIP>75°·DIP<10°, DIP−PIP>50°)에 한한다. 패턴0이 자연스러운 자세 전체를 보증하지 않는다.',
        '', '### 오압현·종료·학습 신호', '',
        f"- audible 오압현 누적 {t['ledger_wrong']:.2f} note-seconds, clean 누적 {t['ledger_clean']:.2f} note-seconds다. 음별 시간의 합이며 환경 벽시계 시간이 아니다. 원인별 press..end 진단(other_higher/own_wrong_fret/own_wrong_string)과 audible 원인행렬은 창이 다르므로 직접 합산하지 않는다.",
        f"- 물리 실패 {f['reasons']['physical_failure']}개 중 기타 회전 플래그{f['reasons'].get('guitar_rotation',0)}회·위치 이탈{f['reasons'].get('guitar_displacement',0)}회다. 한 실패에 여러 플래그가 함께 나타나 합계는 실패 수와 다를 수 있다. 손목 실패{f['reasons']['wrist_failure']}개는 모두 Gy 방향이며 종료 시 clean audible 목표는{t.get('wrist_audible_clean_targets',0):.0f}개였다.",
        f"- raw advantage 표준편차 반복평균은 reward {data['metric_windows']['final']['reward_advantage_std']:.4f}, cost {data['metric_windows']['final']['cost_advantage_std']:.4f}(약 {data['metric_windows']['final']['cost_advantage_std']/data['metric_windows']['final']['reward_advantage_std']:.2f}배)다. 비용 신호가 크다는 관측이며 실제 정책 gradient의 인과·지배 비율로 해석하지 않는다.",
        '- 약지에 성공이 몰리고 검지·중지에는 접촉 달성도 없으므로, 전체 총보상만으로 개선을 판단하기 어렵다. 손목 종료 완화 이후 남은 주요 문제는 손가락별 접근·압현 실패, 대기 대역 미진입, 엄지 목표 접촉 부재, 소지 말단 과굴곡이다.', '']
    matrix=a.get('audible_wrong_source_note_seconds')
    if matrix is not None:
        rows += ['### 실제 audible 오압현 원인 후보','',
            '| 기하 후보 발생 몸체 | 타 손가락 높은 프렛 | 자기 잘못된 프렛 | 자기 잘못된 줄 |',
            '|---|---:|---:|---:|']
        for body,values in zip(data['audible_wrong_source_body_names'],matrix):
            if sum(values)>0:
                rows.append('| '+body+' | '+' | '.join(f'{v:.2f}' for v in values)+' |')
        rows += ['', '단위는 audible 창에서의 source-tagged note-seconds다. 동일 시점에 원인·몸체·음이 겹칠 수 있으므로 표를 합해 전체 오압현 시간이나 점유율로 만들지 않는다. 엄지·검지·중지는 이 원인 후보 집계에서0이었다. 실제 접촉 상대·음향 간섭을 인증한 값은 아니다.','']
    path=OUT/'training_summary.md'
    text=path.read_text().split('\n## 마지막100회 전곡 상세:')[0].rstrip()
    path.write_text(text+'\n'+'\n'.join(rows))


def plot(metrics,groups):
    fig,axs=plt.subplots(2,2,figsize=(14,9),layout='constrained')
    for scope,color in [('phrase','tab:blue'),('full_song','tab:orange')]:
        blocks=sorted((k,v) for k,v in groups.items() if k.startswith('block_') and k.endswith('_'+scope)
            and (scope != 'full_song' or int(k.split('_')[1]) >= 801))
        x=[(int(k.split('_')[1])+min(int(k.split('_')[1])+99,len(metrics)))/2 for k,v in blocks]
        axs[0,0].plot(x,[100*v['success_per_selected_note'] for k,v in blocks],'-o',label=scope,color=color)
        axs[0,1].plot(x,[100*v['reasons'].get('physical_failure',0)/v['episodes'] for k,v in blocks],'-o',label=scope+' physical',color=color)
        axs[0,1].plot(x,[100*v['reasons'].get('wrist_failure',0)/v['episodes'] for k,v in blocks],'--',label=scope+' wrist',color=color)
    axs[0,0].set_ylabel('Achieved / selected notes (%)')
    axs[0,1].set_ylabel('Completed-episode termination (%)')
    for lo in range(0,len(metrics),50):
        rows=metrics[lo:lo+50];x=lo+(len(rows)+1)/2
        for key,color,label in [('song_clean_hold','tab:green','press hold'),('song_finger_standby','tab:purple','standby'),('song_thumb_support','tab:brown','thumb')]:
            axs[1,0].plot(x,60*np.mean([r['reward_component_means'][key] for r in rows]),'o',color=color,label=label if lo==0 else None)
        axs[1,1].plot(x,np.mean([r['diagnostics']['advantages']['reward_raw']['std'] for r in rows]),'o',color='tab:green',label='reward advantage std' if lo==0 else None)
        axs[1,1].plot(x,np.mean([r['diagnostics']['advantages']['cost_raw']['std'] for r in rows]),'o',color='tab:red',label='cost advantage std' if lo==0 else None)
    axs[1,0].set_ylabel('Mean effective reward / simulated second')
    axs[1,1].set_ylabel('Raw advantage standard deviation')
    for ax in axs.flat:
        ax.axvline(750,color='black',ls=':',alpha=.5)
        ax.set_xlabel('PPO update (1-based)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Large / 1024 environments / 1478 updates — training, not fixed-policy evaluation')
    fig.savefig(OUT/'training_trends.png',dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    main()
