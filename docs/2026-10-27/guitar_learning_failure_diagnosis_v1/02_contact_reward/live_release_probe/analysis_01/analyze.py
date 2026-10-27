"""CPU-only independent recomputation of sealed run_01; raw evidence is read-only."""
import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', '/tmp/live_release_analysis_mpl')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
RUN = HERE.parent/'run_01'


def read(name):
    return json.loads((RUN/name).read_text())


def write(name, value):
    (HERE/name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def longest(mask, clock):
    indices = np.flatnonzero(mask)
    if not len(indices):
        return dict(stable_release_50ms=False, max_contiguous_span_s=0.,
            max_contiguous_samples=0, start_clock=None, end_clock=None)
    # Separate implementation: split eligible indices into observed consecutive runs.
    split = np.flatnonzero((np.diff(indices) != 1) | (np.diff(clock[indices]) != 1))+1
    runs = np.split(indices, split)
    best = max(runs, key=len)
    start, end = int(clock[best[0]]), int(clock[best[-1]])
    return dict(stable_release_50ms=end-start >= 12, max_contiguous_span_s=(end-start)/240.,
        max_contiguous_samples=len(best), start_clock=start, end_clock=end)


def main():
    raw_before = {str(p): digest(p) for p in RUN.iterdir() if p.is_file()}
    report, native, scene = read('probe_report.json'), read('report.json'), read('gpu_scene_final.json')
    episodes = sorted(read('first_attempt_episodes.json'), key=lambda e: e['env_id'])
    settings, contract = read('settings.json'), read('training_contract.json')
    spec = settings['song']['short_learning']
    view, index = spec['view'], spec['view']['source_index']
    press, onset, end = (view[key] for key in ('local_press_s', 'local_onset_s', 'local_end_s'))
    duration = end-onset
    a, c = np.load(RUN/'physics240.npz'), np.load(RUN/'control60.npz')
    data, controls = {k: a[k] for k in a.files}, {k: c[k] for k in c.files}
    a.close(); c.close()
    assert [e['env_id'] for e in episodes] == list(range(128))
    assert all(report['checks'].values()) and report['completed'] and native['completed']
    assert scene['closed'] and scene['physics_steps'] == len(data['clock']) == 872
    assert len(data['clock']) == 4*len(controls['clock'])
    assert all(np.isfinite(v).all() for v in [*data.values(), *controls.values()])
    assert np.array_equal(data['candidate'], data['positive'] & ~data['wrong'])
    assert all(np.array_equal(data['clock'][data['first_attempt'][:, i], i],
        np.arange(1, int(data['first_attempt'][:, i].sum())+1)) for i in range(128))
    assert not np.any(~data['first_attempt'][:-1] & data['first_attempt'][1:])
    # Full first attempts are contiguous prefixes here, so cumulative loss cannot cross reset.
    force = np.linalg.norm(data['distal_force_n'], axis=-1)
    terms = contract['reward']['active_terms']
    assert len(terms) == 9
    errors = {key: [] for key in ('ledger_clean', 'ledger_wrong', 'ledger_missing', 'ledger_best_clean_streak',
        'ledger_contact_progress', 'ledger_contact_time', 'contact_formula', 'hold_formula',
        'achievement_formula', 'wrong_formula', 'performance_formula', 'nine_sum', 'control_sum',
        'control_component_sum', 'final_component')}
    cases, mismatch = [], []
    for i, episode in enumerate(episodes):
        live, clock = data['first_attempt'][:, i], data['clock'][:, i]
        t = data['local_time_s'][:, i]
        candidate, wrong = data['candidate'][:, i], data['wrong'][:, i]
        previous = np.r_[False, candidate[:-1]]
        previous_wrong = np.r_[False, wrong[:-1]]
        requested = data['release_requested'][:, i]
        adjacent = np.r_[False, np.diff(clock) == 1]
        loss = live & requested & previous & ~candidate & adjacent
        eligible = live & requested & (np.cumsum(loss) > 0) & ~candidate & ~data['geometry'][:, i] & (force[:, i] < .01)
        stable = longest(eligible, clock)
        joint = bool(eligible.any())
        note, rewards = episode['live_selected_note'], episode['reward_components']
        window = live & (t >= press) & (t <= end)
        progress = data['note_contact_progress'][:, i]
        short = bool(0 < note['contact_progress'] < 1 and not note['left'] and
            np.any(window & (progress > 0) & (progress < 1)))
        saved = report['witnesses'][i]
        if (short != saved['short_only_witness'] or stable != saved['stable_release'] or
                joint != saved['geometry_absent_candidate_loss_load_low_same_sample']):
            mismatch.append(i)
        before_t = t-1/240.
        audible_overlap = np.maximum(0., np.minimum(t, end)-np.maximum(before_t, onset))*live
        press_overlap = np.maximum(0., np.minimum(t, end)-np.maximum(before_t, press))*live
        both = candidate & previous
        clean = float(np.sum(audible_overlap*both))
        wrong_time = float(np.sum(audible_overlap*.5*(wrong.astype(float)+previous_wrong)))
        missing_time = float(np.sum(audible_overlap*.5*((~candidate & ~wrong).astype(float)+(~previous & ~previous_wrong))))
        clean_streak, contact_streak, best_clean, best_contact = 0., 0., 0., 0.
        for good, audible_dt, press_dt in zip(both, audible_overlap, press_overlap):
            clean_streak = clean_streak+audible_dt if good and audible_dt > 0 else 0.
            contact_streak = contact_streak+press_dt if good and press_dt > 0 else 0.
            best_clean, best_contact = max(best_clean, clean_streak), max(best_contact, contact_streak)
        required = episode['left_note_ledger']['required_clean_s'][index]
        reconstructed = dict(clean=clean, wrong=wrong_time, missing=missing_time,
            best_clean_streak=best_clean, contact_progress=min(best_contact/min(.05, end-press), 1),
            contact_time=float(np.sum(press_overlap*both)))
        for key, value in reconstructed.items():
            errors['ledger_'+key].append(abs(note[key]-value))
        assert bool(note['left']) == bool(best_clean+1e-12 >= required)
        release_edges = live & previous & ~candidate & (t >= end) & (t <= end+.1)
        assert bool(note['released']) == bool(release_edges.any())
        if release_edges.any():
            first_release = int(np.flatnonzero(release_edges)[0])
            assert abs(note['release_s']-data['source_time_s'][first_release, i]) < 1e-12
        for key in ('contact_progress', 'clean', 'clean_streak', 'best_clean_streak', 'left', 'released', 'release_s'):
            assert abs(float(data['note_'+key][live, i][-1])-float(note[key])) < 1e-12
        expected = dict(contact_formula=.25*note['contact_progress'], hold_formula=note['clean']/duration,
            achievement_formula=.25*bool(note['left']), wrong_formula=-.15*note['wrong']/duration,
            performance_formula=-.1*max(note['missing']/duration, max(0., 1-note['best_clean_streak']/required)))
        names = ['song_left_contact', 'song_clean_hold', 'song_left_success', 'song_wrong_press', 'song_performance_deficit']
        safe = not (episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
        if safe:
            for (key, value), name in zip(expected.items(), names):
                errors[key].append(abs(rewards[name]-value))
        assert -.15-5e-6 <= rewards['song_wrong_press'] <= 5e-6
        assert -.10-5e-6 <= rewards['song_performance_deficit'] <= 5e-6
        assert 0 <= rewards['song_left_contact'] <= .25+5e-6
        assert 0 <= rewards['song_clean_hold'] <= 1+5e-6
        assert 0 <= rewards['song_left_success'] <= .25+5e-6
        assert 0 <= rewards['song_finger_standby'] <= .02*episode['steps']/60+5e-6
        assert 0 <= rewards['song_thumb_support'] <= .02*episode['steps']/60+5e-6
        assert rewards['action_change'] <= 0
        errors['nine_sum'].append(abs(sum(rewards.values())-episode['reward']))
        control_live = controls['first_attempt'][:, i]
        errors['control_sum'].append(abs(controls['reward'][control_live, i].astype(float).sum()-episode['reward']))
        summed = np.zeros(int(control_live.sum()), dtype=np.float64)
        for name in terms:
            values = controls['reward_increment_'+name][control_live, i].astype(float)
            errors['control_component_sum'].append(abs(values.sum()-rewards[name]))
            errors['final_component'].append(abs(controls['reward_cumulative_'+name][control_live, i][-1]-rewards[name]))
            summed += values
        errors['control_component_sum'].append(float(np.max(np.abs(summed-controls['reward'][control_live, i]))))
        release_rows = np.flatnonzero(live & requested)
        start_row = int(release_rows[0]) if len(release_rows) else None
        stable_rows = (clock >= stable['start_clock']) & (clock <= stable['end_clock']) & live if stable['start_clock'] is not None else np.zeros_like(live)
        motion = dict(q4_range_rad=np.ptp(data['q4'][live, i], axis=0).tolist(),
            target4_range_rad=np.ptp(data['target4'][live, i], axis=0).tolist(),
            distal_resultant_max_n=float(force[live, i].max()))
        if start_row is not None:
            motion.update(request_start_clock=int(clock[start_row]), actual_q4_change_from_request_rad=(data['q4'][live, i][-1]-data['q4'][start_row, i]).tolist())
        if stable_rows.any():
            motion.update(stable_distal_resultant_max_n=float(force[stable_rows, i].max()),
                stable_surface_distance_min_m=float(data['surface_distance_m'][stable_rows, i].min()),
                stable_surface_distance_max_m=float(data['surface_distance_m'][stable_rows, i].max()),
                stable_surface_height_min_m=float(data['surface_height_m'][stable_rows, i].min()),
                stable_surface_height_max_m=float(data['surface_height_m'][stable_rows, i].max()),
                stable_distal_position_span_m=np.ptp(data['distal_pose'][stable_rows, i, :3], axis=0).tolist())
        cases.append(dict(env_id=i, condition=i % 16, safe=safe, reason=episode['reason'],
            physical_failure=episode['termination']['physical_failure'], wrist_failure=episode['termination']['wrist_failure'],
            achieved=bool(note['left']) and safe, short_only=short and safe, joint=joint and safe,
            stable_release=stable, stable_success=stable['stable_release_50ms'] and safe,
            clean_fraction=note['clean']/duration, wrong_fraction=note['wrong']/duration,
            native_note_released=bool(note['released']), note=note, motion=motion, rewards=rewards))
    maxima = {key: max(values, default=0.) for key, values in errors.items()}
    assert not mismatch and max(maxima.values()) < 5e-6, (mismatch, maxima)
    summaries = []
    for condition, release_s in enumerate(report['protocol']['release_s']):
        group = [case for case in cases if case['condition'] == condition]
        summaries.append(dict(condition=condition, release_s=release_s, assigned=8, completed=len(group),
            physical_failure=sum(x['physical_failure'] for x in group), wrist_failure=sum(x['wrist_failure'] for x in group),
            achieved=sum(x['achieved'] for x in group), short_only=sum(x['short_only'] for x in group),
            joint=sum(x['joint'] for x in group), stable50ms=sum(x['stable_success'] for x in group),
            native_released=sum(x['native_note_released'] for x in group),
            mean_clean_fraction=float(np.mean([x['clean_fraction'] for x in group])),
            mean_wrong_fraction=float(np.mean([x['wrong_fraction'] for x in group])),
            stable_span_median_s=float(np.median([x['stable_release']['max_contiguous_span_s'] for x in group]))))
    write('cases.json', cases); write('condition_summary.json', summaries)
    with (HERE/'condition_summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0])); writer.writeheader(); writer.writerows(summaries)
    input_after = read('inputs_after.json')
    assert input_after['verified'] and not input_after['changed_paths'] and not input_after['unpinned_project_sources']
    assert all(Path(name).is_file() and digest(Path(name)) == value for name, value in input_after['input_pins'].items())
    assert raw_before == {str(p): digest(p) for p in RUN.iterdir() if p.is_file()}
    verification = dict(completed=True, cpu_only=True, gpu_executed_by_analysis=False,
        independently_recomputed_cases=128, witness_report_mismatches=mismatch, maximum_absolute_errors=maxima,
        raw_inputs_unchanged=True, source_pins_still_valid=True, source_pin_count=len(input_after['input_pins']),
        launcher_exit_not_captured=True, launcher_session='64709 expired before final poll; Unknown process id',
        scene_completion_verified_independently=True, host_reboot=False,
        host_boot_evidence_source='root supplied unchanged boot observation; not derivable from native result artifacts alone',
        scene_closed=scene['closed'], physics_steps=scene['physics_steps'], control_ticks=len(controls['clock']),
        provenance='independent NumPy run segmentation and actual endpoint ledger integration; does not import probe.py',
        achievement_and_native_release_independently_recomputed=True,
        reward_tolerance=5e-6, approach_limitation='Nine-term trace/ledger totals verified; Phi0/reset potential not captured, so no independent PBRS telescoping proof',
        raw_input_sha256=raw_before)
    write('verification.json', verification)
    make_plot(data, force, summaries, cases, view)
    make_results(summaries, cases, verification, native, duration)


def make_plot(data, force, summary, cases, view):
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5), constrained_layout=True)
    x = np.arange(16); width=.25
    for offset, key, label, color in [(-1,'achieved','Achieved','#2878b5'),(0,'short_only','Short only','#e69f00'),(1,'stable50ms','Stable release >=50ms','#15976b')]:
        axes[0,0].bar(x+offset*width, [row[key] for row in summary], width, label=label, color=color)
    axes[0,0].set(xticks=x, ylabel='Safe witnesses / 8 assigned attempts', title='All conditions; no physical/wrist failures', ylim=(0,9))
    axes[0,0].legend(fontsize=8, loc='upper left')
    axes[0,1].plot(x,[100*row['mean_clean_fraction'] for row in summary],'o-',label='Clean',color='#2878b5')
    axes[0,1].plot(x,[100*row['mean_wrong_fraction'] for row in summary],'o-',label='Wrong',color='#c64747')
    axes[0,1].set(xticks=x, ylabel='Mean original audible window (%)', ylim=(0,105), title='0 = no release; 1..15 = fixed release schedule')
    axes[0,1].legend(fontsize=8)
    i=next(case['env_id'] for case in cases if case['short_only'])
    t=data['local_time_s'][:,i]; m=(t>=2.90)&(t<=3.35)
    for j,color in enumerate(('#2878b5','#e69f00','#15976b','#9954a0')):
        axes[1,0].plot(t[m],data['q4'][m,i,j],color=color,label=f'q{j+1}')
        axes[1,0].plot(t[m],data['target4'][m,i,j],color=color,linestyle='--',alpha=.55)
    axes[1,0].set(title=f'Env {i}: first short-only witness; q solid / target dashed',xlabel='Actual local time (s)',ylabel='Joint angle (rad)')
    axes[1,0].legend(fontsize=8,ncol=4)
    axes[1,1].plot(t[m],force[m,i],color='#444444',label='Assigned distal resultant')
    axes[1,1].axhline(.01,ls=':',color='#c64747',label='Original 0.01 N gate')
    axes[1,1].set(title=f'Env {i}: actual native body load and candidate',xlabel='Actual local time (s)',ylabel='Resultant force (N)')
    twin=axes[1,1].twinx();twin.step(t[m],data['candidate'][m,i].astype(int),where='post',color='#2878b5',alpha=.6)
    twin.set(ylim=(-.05,1.2),yticks=[0,1],ylabel='Clean candidate')
    axes[1,1].legend(fontsize=8)
    for ax in axes.flat:
        ax.grid(alpha=.2)
    for ax in axes[1]:
        ax.axvspan(view['local_onset_s'],view['local_end_s'],color='#2878b5',alpha=.08)
    fig.suptitle('Finite reference diagnostic, fixed guitar / middle row8 / 128 first attempts',fontsize=12)
    fig.savefig(HERE/'condition_summary.png',dpi=160)
    plt.close(fig)


def make_results(summary,cases,verification,native,duration):
    total=lambda key: sum(row[key] for row in summary)
    table='\n'.join('| '+ ' | '.join(map(str,[row['condition'], '유지' if row['release_s'] is None else f"{row['release_s']:.2f}",
        f"{row['achieved']}/8",f"{row['short_only']}/8",f"{row['stable50ms']}/8",f"{100*row['mean_clean_fraction']:.1f}",
        f"{100*row['mean_wrong_fraction']:.1f}",f"{1000*row['stable_span_median_s']:.1f}"]))+' |' for row in summary)
    examples=[]
    for i in [6,9]:
        case=cases[i];note=case['note'];stable=case['stable_release'];motion=case['motion']
        examples.append(f"- env{i} / 조건{case['condition']}: contact_progress={note['contact_progress']:.6f}, clean={1000*note['clean']:.3f}ms, best clean streak={1000*note['best_clean_streak']:.3f}ms, 달성={note['left']}. "
            f"실제 연속 해제 관측 clock{stable['start_clock']}→{stable['end_clock']} ({stable['start_clock']/240:.6f}→{stable['end_clock']/240:.6f}s), span={1000*stable['max_contiguous_span_s']:.3f}ms. "
            f"그 구간 말단 합력 최대{motion['stable_distal_resultant_max_n']:.6g}N, 표면거리{1000*motion['stable_surface_distance_min_m']:.3f}→{1000*motion['stable_surface_distance_max_m']:.3f}mm. "
            f"contact/hold/achievement 보상={case['rewards']['song_left_contact']:.6f}/{case['rewards']['song_clean_hold']:.6f}/{case['rewards']['song_left_success']:.6f}.")
    terms=list(cases[0]['rewards'])
    reward_table='\n'.join(f"| `{name}` | {min(c['rewards'][name] for c in cases):.6f} | {max(c['rewards'][name] for c in cases):.6f} |" for name in terms)
    text=f'''# 실제 시계 짧은 접촉·해제 진단 결과

고정 기타·중지 row8의 사전 지정128개 첫 시도에서 **짧은 접촉만17/128, 연속50ms 이상 해제 관측95/128, 음악 달성53/128**을 확보했다. 세 범주는 겹치므로 합산하지 않는다. 짧은 접촉만17개 중16개에는 연속50ms 이상 해제 관측도 있다. 물리 실패0/128, 손목 실패0/128이다. 이는 봉인한 reference를 유한 제어한 진단이며 정책 학습 성과·자유 기타 성능·실제 현 압력 인증이 아니다.

## 조건별 결과

조건0은 reference 유지, 조건1~15는 사전 지정 시간에 중지4축만035 목표로 회수한다. 아래 성공 분자는 물리·손목 실패를 제외하고 분모는 배정된8개를 그대로 쓴다. 이번에는 실패가 없어서 제외되는 사례가 없다. 기타·팔 안내·다른 손가락 B·범위·PD·보상·판정은 원래 계약을 유지했다. 회수 시점은 다음60Hz endpoint 기준이며 실제 회수 요청과 상태는240Hz 원자료에 기록했다.

| 조건 | 회수 요청(s) | 달성 | 짧은 접촉만 | 해제≥50ms | 평균 clean(%) | 평균 wrong(%) | 최대 해제 span의 중앙값(ms) |
| --- | --- | --- | --- | --- | --- | --- | --- |
{table}

![조건별 결과와 실제 중지 관절·말단 부하](condition_summary.png)

원음 press2.9787s, onset3.0s, end3.1174s, audible 길이{1000*duration:.1f}ms, 연속 달성 문턱50ms다. 짧은 접촉만은 최종 `0<contact_progress<1`, 원 press..end 창 안의 실제 중간 progress, 최종 미달성을 모두 요구했다. 준비 창에서만 짧게 접촉하면 clean·hold 보상은0일 수 있으며, 그 자체를 짧은 접촉의 정의로 사용하지 않았다. 조건7의 일부는 contact_progress=1이어도 연속 audible clean50ms에 못 미쳐 달성되지 않았다.

해제는 실제 회수 요청 후 candidate true→false를 관측한 다음, candidate 없음·원래 pad 위치 기하 없음·할당 말단 합력<0.01N이 연속되는 구간으로 계산했다. 보수적 span은 `(마지막clock−첫clock)/240`이며13개 연속 endpoint부터50ms다. 한 표본 동시 증거도{total('joint')}/128로 같은 수였지만, 그 사실만으로50ms를 가정하지 않고 NPZ에서 연속 구간을 별도 재계산했다. native note의 `released`는{total('native_released')}/128이다. 이 flag는 원래 음 종료 뒤0.1초 안의 candidate 소실만 기록하므로, 음 종료 전에 실제로 회수된 사례에는 false가 남을 수 있다.

## 실제 구간·관절·부하 예

아래 사례는 사전 지정 전체 분모를 바꾸지 않는 설명용이다. env6은 결과에서 처음 확인된 짧은 접촉만 사례이며, env9는 달성과 해제가 함께 있는 예다. 전체128개 값과 q4/목표 변화 범위는 [cases.json](cases.json)에 모두 남겼다. 그래프는 env6의 실제 q4와 유한 목표를 함께 표시하며 상태를 덮어쓴 궤적이 아니다.

{chr(10).join(examples)}

## 실제 보상 원장 검산

선택된 원음1개·존재 손가락1개이므로 균형계수b=1이다. 모든128개에서 원장과 실제9개 누적 보상·60Hz 증분 합을 대조했다. 접촉=`0.25×contact_progress`(상한0.25), 유지=`clean/D`(상한1), 달성=`0.25×left`(한 번), wrong=`−0.15×wrong/D`(하한−0.15), 부족=`−0.10×max(missing/D, 1−best_clean_streak/required)`(하한−0.10)를 확인했다. 최초접촉 보상을 반복 지급하거나 부족 정산을 중복 가산한 초과는 없었다. raw240Hz 인접 candidate와 원래 창 overlap으로 clean/wrong/missing·접촉 progress·streak도 독립 적분했다. 검산 최대오차는 [verification.json](verification.json)에 항목별로 기록했으며 모두5×10⁻⁶ 미만이다.

| 실제9항 | 최소 | 최대 |
| --- | --- | --- |
{reward_table}

standby·thumb는 원래0.02/s 상한, action_change는 비양수임을 확인했다. 접근 보상은9항 합과60Hz 증분/누적 원장 일치까지 확인했다. Φ0와 reset potential을 기록하지 않았으므로 별도의 PBRS telescoping 입증을 주장하지 않으며, 비할인 접근 보상 합을 기하 접근 품질 지표로 해석하지 않는다. 모든 음 성공/실패·정상 미달성·회수 실패를 [condition_summary.csv](condition_summary.csv)와 전체 원장에 포함했다.

## 무결성·실행 종료 및 남은 범위

독립 NumPy 재계산128개에서 짧은 접촉·한 표본 해제·최대 연속 span·50ms flag가 원 보고서와 모두 일치했다. 실제872개 물리 endpoint /218개 제어 tick, 정확히4 substeps/control, 유한 값, 연속 시계,12개 원 실행 audit를 확인했다. 현재 입력 pin{verification['source_pin_count']}개와 원자료 SHA를 다시 확인했고 원파일은 수정하지 않았다. 체크포인트 모델/버퍼 동일·업데이트0·GPU 장면1개/128환경·장면 종료 true가 원 실행 보고서에 남아 있다.

원 실행 wall={native['wall_s']:.3f}s. 도구 세션64709가 최종 poll 전에 만료되어 **launcher exit code는 수집하지 못했다**. `Unknown process id`를 호스트 재부팅으로 해석하지 않는다. 호스트 boot가 같다는 root 확인과 별개로, 원 report·실제 NPZ·GPU scene final의 완료/종료를 독립 확인했다. 이 도구 종료 수집 한계는 유지하며 재실행으로 덮지 않았다.

추가 CPU 조사로, 기존 negative audit에 미리 선언된 `할당 말단 합력≥0.01N & pad 위치 기하=true & 같은 유효 표본의 facing 기하=false` 조건을 이번 캡처 전체에 적용했다. 이는 release 결과를 사전에 지정한 조건이라고 소급하지 않는 **캡처 후 분석**이다. 전체111,616개 첫 시도 표본, 원 press..end 안4352개 endpoint, audible 창 안3712개 endpoint에서 일치0개였다. 원래 적분 창과 양의 overlap을 갖는 구간도 따로 검사했으며0개였다. 저장된 중지 말단·기타 pose와 봉인된 palmar pad 표본·원래 줄/프렛/평면에서 기하·facing을 독립 재구성했고, 전체 표본에서 두 flag 불일치0개·거리 최대오차4.20×10⁻⁸m였다. 따라서 `(clock,env_id)`순 첫 qualifying witness는 없다. 자세/힘/판정 문턱을 만들어 채우지 않았다. 자세한 분모와 입력 SHA는 [facing_negative_audit.json](facing_negative_audit.json)에 있다.

이번 결과로 실제 악보 시계의 짧은 접촉·후속 유한 해제 증거는 확보했다. 잘못된 패드 방향(facing-negative)을 별도 도달·통제한 사례는 아직 없다. 잘못된 줄/프렛·다른 손가락 간섭·모든 손가락 대표 음의 검증이나 전곡 전환이 완료됐다는 뜻도 아니다. GPU 말단 합력은 접촉 상대 pair를 특정하지 못하며, pad 기하·candidate·하중 소실을 실제 현 압력·진동·소리의 인증으로 확대하지 않는다.
'''
    (HERE/'RESULTS.md').write_text(text)


if __name__ == '__main__':
    main()
