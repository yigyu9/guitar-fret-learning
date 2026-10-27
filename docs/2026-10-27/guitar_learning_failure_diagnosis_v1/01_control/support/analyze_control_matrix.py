"""Read-only CPU analysis of the predeclared native 84-row control matrix."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

MODES = ('incremental', 'position')
FINGERS = ('index', 'middle', 'ring', 'pinky')
RAD_TO_DEG = 180 / np.pi


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite_stats(values):
    values = np.asarray(values)
    if not values.size:
        return dict(count=0, mean=None, median=None, p95=None, maximum=None)
    if not np.isfinite(values).all():
        raise ValueError('Nonfinite diagnostic data')
    return dict(count=int(values.size), mean=float(values.mean()),
                median=float(np.median(values)), p95=float(np.percentile(values, 95)),
                maximum=float(values.max()))


def longest(mask, hz):
    edges = np.diff(np.r_[False, np.asarray(mask, bool), False].astype(int))
    starts, ends = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return float((ends - starts).max() / hz) if len(starts) else 0.


def occupancy(mask, valid, hz):
    accepted = np.asarray(mask, bool) & valid
    n = int(valid.sum())
    return dict(samples=int(accepted.sum()), eligible_samples=n,
                fraction=float(accepted.sum() / n) if n else None,
                sampled_duration_s=float(accepted.sum() / hz),
                longest_consecutive_samples_s=longest(accepted, hz))


def load_run(root, mode):
    run = root / mode
    report = json.loads((run / 'report.json').read_text())
    settings = json.loads((run / 'settings.json').read_text())
    if report.get('completed') is not True or report.get('changed_inputs'):
        raise ValueError('Completed source-verified native run required: ' + str(run))
    if settings['mode'] != mode or report['mode'] != mode:
        raise ValueError('Mode mismatch')
    with np.load(run / 'trace60.npz', allow_pickle=False) as f:
        slow = {k: f[k].copy() for k in f.files}
    with np.load(run / 'trace240.npz', allow_pickle=False) as f:
        fast = {k: f[k].copy() for k in f.files}
    cases, names = settings['cases'], report['joint_names']
    expected = [(p, n, s) for p in ('target_path', 'output_bias') for n in names for s in (-1, 1)]
    actual = [(c['protocol'], c['joint'], c['sign']) for c in cases]
    if len(names) != 21 or len(cases) != 84 or actual != expected:
        raise ValueError('Predeclared21-joint/both-sign/two-protocol cases required')
    if slow['q'].shape != (721, 84, 21) or fast['actual_selected'].shape != (2880, 84):
        raise ValueError('Complete12-second traces required, even when some rows fail')
    np.testing.assert_allclose(slow['tick'], np.arange(721), atol=0, rtol=0)
    np.testing.assert_allclose(fast['time_s'], np.arange(1, 2881) / 240, atol=1e-12, rtol=0)
    for key in ('actual_selected', 'target_selected', 'qd_selected', 'hand_net_force_max', 'effort_selected'):
        if not np.isfinite(fast[key]).all():
            raise ValueError('Nonfinite trace: ' + key)
    if np.any(np.diff(fast['alive'].astype(int), axis=0) > 0):
        raise ValueError('Censored row became alive again')
    return dict(run=run, report=report, settings=settings, slow=slow, fast=fast)


def analyze(data):
    report, settings, slow, fast = (data[k] for k in ('report', 'settings', 'slow', 'fast'))
    time60, time240 = slow['tick'] / 60., fast['time_s']
    low, high, b = (np.array(report[k]) for k in ('native_lower', 'native_upper', 'B_target_rad'))
    names, rows = report['joint_names'], []
    windows = dict(positive_hold=(3., 4.), reverse_hold=(5.5, 6.))
    for case in settings['cases']:
        row, joint = case['row'], names.index(case['joint'])
        valid240, valid60 = fast['alive'][:, row], slow['alive'][:, row]
        actual, target = fast['actual_selected'][:, row], fast['target_selected'][:, row]
        value = dict(case, failure=report['failure_reasons'][row],
                     accepted_physics_samples=int(valid240.sum()), total_physics_samples=len(time240))
        initial = (time240 <= 1. + 1e-12) & valid240
        value['initial_hold240'] = dict(window_s=[0., 1.], expected_samples=240,
            fully_observed=bool(initial.sum() == 240),
            selected_tracking_abs_deg=finite_stats(np.abs(actual[initial] - target[initial]) * RAD_TO_DEG),
            selected_speed_abs_rad_s=finite_stats(np.abs(fast['qd_selected'][initial, row])))
        value['tracking_windows'] = {}
        if case['protocol'] == 'target_path':
            for label, (start, end) in windows.items():
                mask = (time240 >= start - 1e-12) & (time240 <= end + 1e-12)
                valid = mask & valid240
                stats = finite_stats(np.abs(actual[valid] - target[valid]) * RAD_TO_DEG)
                stats.update(window_s=[start, end], expected_samples=int(mask.sum()),
                             fully_observed=bool(valid.sum() == mask.sum()),
                             p95_le_10deg=bool(stats['p95'] <= 10) if stats['p95'] is not None else None)
                value['tracking_windows'][label] = stats
        for label, begin, end in [('bias_forward', 1., 6.)] if case['protocol'] == 'output_bias' else []:
            first, last = round(begin * 60), round(end * 60)
            complete = bool(valid60[first:last + 1].all())
            q0, q1 = slow['q'][[first, last], row, joint]
            t0, t1 = slow['target'][[first, last], row, joint]
            action = slow['action'][first + 1:last + 1, row, joint]
            value[label] = dict(window_s=[begin, end], fully_observed=complete,
                target_change_deg=float((t1 - t0) * RAD_TO_DEG) if complete else None,
                actual_change_deg=float((q1 - q0) * RAD_TO_DEG) if complete else None,
                action_mean=float(action.mean()) if complete else None,
                action_time_integral=float(action.sum() / 60) if complete else None,
                incremental_unclamped_requested_change_deg=float(case['sign'] * .05 * 4 * 5 * RAD_TO_DEG)
                if settings['mode'] == 'incremental' else None,
                interpretation='incremental: signed0.05 requests0.2rad/s; position: signed0.05 requests one fixed reference-relative angle')
        start, end = (6., 7.) if case['protocol'] == 'target_path' else (8., 9.)
        first, last = round(start * 60), round(end * 60)
        complete = bool(valid60[first:last + 1].all())
        value['raw_zero'] = dict(window_s=[start, end], fully_observed=complete,
            target_change_deg=float((slow['target'][last, row, joint] - slow['target'][first, row, joint]) * RAD_TO_DEG) if complete else None,
            actual_change_deg=float((slow['q'][last, row, joint] - slow['q'][first, row, joint]) * RAD_TO_DEG) if complete else None,
            final_target_from_initial_reference_deg=float((slow['target'][last, row, joint] - slow['target'][0, row, joint]) * RAD_TO_DEG) if complete else None)
        value['selected_axis_limits240'] = {}
        for label, q in [('actual', actual), ('target', target)]:
            margin = np.minimum(q - low[joint], high[joint] - q)
            value['selected_axis_limits240'][label] = dict(
                beyond_native_1e_6=occupancy(margin < -1e-6, valid240, 240),
                boundary_or_beyond_1e_6=occupancy(margin <= 1e-6, valid240, 240),
                engineering_near_1deg=occupancy(margin <= np.pi / 180, valid240, 240),
                maximum_native_excess_deg=float(np.maximum(-margin[valid240], 0).max() * RAD_TO_DEG) if valid240.any() else None)
        value['all_hand_axes_limits60'] = {}
        for label in ('q', 'target'):
            margin = np.minimum(slow[label][:, row] - low, high - slow[label][:, row])
            # Exclude reset t0. This is a sampled60Hz statistic, not a240Hz extreme.
            valid = valid60.copy(); valid[0] = False
            value['all_hand_axes_limits60']['actual' if label == 'q' else label] = {
                name: dict(beyond_native_1e_6=occupancy(margin[:, j] < -1e-6, valid, 60),
                           engineering_near_1deg=occupancy(margin[:, j] <= np.pi / 180, valid, 60))
                for j, name in enumerate(names)}
        bmask = (time60 >= 11.5 - 1e-12) & (time60 <= 12. + 1e-12)
        valid = bmask & valid60
        value['B_final60'] = dict(window_s=[11.5, 12.], expected_frames=int(bmask.sum()),
            accepted_frames=int(valid.sum()), fully_observed=bool(valid.sum() == bmask.sum()), fingers={})
        for finger in FINGERS:
            cols = [j for j, n in enumerate(names) if n.startswith('LH:' + finger)]
            error = (slow['q'][valid, row][:, cols] - b[cols]) * RAD_TO_DEG
            target_error = (slow['target'][valid, row][:, cols] - b[cols]) * RAD_TO_DEG
            rms = float(np.sqrt(np.mean(error ** 2))) if error.size else None
            maximum = float(np.abs(error).max()) if error.size else None
            value['B_final60']['fingers'][finger] = dict(joints=[names[j] for j in cols],
                scalar_samples=int(error.size), actual_rms_deg=rms, actual_max_abs_deg=maximum,
                target_max_abs_deg=float(np.abs(target_error).max()) if error.size else None,
                diagnostic_pass=bool(value['B_final60']['fully_observed'] and rms <= 10 and maximum <= 20)
                if error.size else False)
        value['selected_axis_motion240'] = dict(speed_abs_rad_s=finite_stats(np.abs(fast['qd_selected'][valid240, row])))
        value['hand_net_force_max240_n'] = finite_stats(fast['hand_net_force_max'][valid240, row])
        value['submitted_external_effort240'] = finite_stats(np.abs(fast['effort_selected'][valid240, row]))
        rows.append(value)
    tracking = [v for r in rows for v in r['tracking_windows'].values()]
    complete_tracking = [v for v in tracking if v['fully_observed']]
    bchecks = [v for r in rows for v in r['B_final60']['fingers'].values()]
    return dict(mode=settings['mode'], guitar=settings.get('guitar'), rows=rows, summary=dict(
        total_cases=len(rows), failed_cases=report['failed'],
        tracking_windows_planned=len(tracking), tracking_windows_complete=len(complete_tracking),
        tracking_windows_complete_p95_le_10deg=sum(v['p95_le_10deg'] for v in complete_tracking),
        complete_tracking_p95_deg=finite_stats([v['p95'] for v in complete_tracking]),
        B_row_finger_checks_planned=len(bchecks), B_checks_pass=sum(v['diagnostic_pass'] for v in bchecks),
        B_rows_complete=sum(r['B_final60']['fully_observed'] for r in rows),
        maximum_target_speed_rad_s=report['maximum_target_speed_rad_s'],
        max_incremental_codec_error_rad=report['max_incremental_codec_error_rad'],
        maximum_observed_actual_native_excess_deg=max(r['selected_axis_limits240']['actual']['maximum_native_excess_deg'] or 0 for r in rows)))


def plots(root, data, analysis):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'Noto Sans CJK JP', 'axes.unicode_minus': False})
    output = []
    names, cases = data['report']['joint_names'], data['settings']['cases']
    slow = data['slow']; time60 = slow['tick'] / 60.
    colors = {-1: '#2b6cb0', 1: '#c05621'}
    for protocol in ('target_path', 'output_bias'):
        fig, axes = plt.subplots(7, 3, figsize=(17, 23), sharex=True)
        for joint, ax in enumerate(axes.flat):
            channel = names[joint]
            twin = ax.twinx()
            for c in cases:
                if c['protocol'] != protocol or c['joint'] != channel:
                    continue
                row, sign = c['row'], c['sign']; valid = slow['alive'][:, row]
                def masked(key):
                    return np.where(valid, slow[key][:, row, joint], np.nan)
                label = '+' if sign == 1 else '−'
                ax.plot(time60, masked('q') * RAD_TO_DEG, color=colors[sign], label=label+' 실제각')
                ax.plot(time60, masked('target') * RAD_TO_DEG, '--', color=colors[sign], alpha=.75, label=label+' 목표각')
                twin.plot(time60, masked('action'), ':', color=colors[sign], alpha=.35)
            ax.set_title(channel, fontsize=10); ax.grid(alpha=.2); ax.set_ylabel('각도(°)')
            twin.set_ylim(-1.05, 1.05); twin.set_ylabel('행동', fontsize=8)
            ax.axvspan(10, 12, color='#38a169', alpha=.07)
            if joint >= 18: ax.set_xlabel('시간(초)')
        axes.flat[0].legend(fontsize=7, ncol=2)
        fig.suptitle(analysis['mode']+' / '+protocol+'\n실제각·목표각, 점선 보조축=행동; 실패 이후 제외; 녹색=B 유지', fontsize=15)
        fig.tight_layout(rect=[0, 0, 1, .965], w_pad=3.0)
        path = root/('analysis_'+analysis['mode']+'_'+protocol+'.png')
        fig.savefig(path, dpi=140); plt.close(fig); output.append(str(path))
    values = np.array([[r['B_final60']['fingers'][f]['actual_rms_deg'] if r['B_final60']['fully_observed'] else np.nan
                        for f in FINGERS] for r in analysis['rows']])
    fig, ax = plt.subplots(figsize=(7, 16))
    im = ax.imshow(values, aspect='auto', vmin=0, vmax=max(20., float(np.nanmax(values))) if np.isfinite(values).any() else 20.)
    ax.set_xticks(range(4)); ax.set_xticklabels(['검지', '중지', '약지', '소지'])
    ax.set_yticks(range(84)); ax.set_yticklabels([f"{r['row']:02} {r['joint']} {r['sign']:+}" for r in analysis['rows']], fontsize=6)
    ax.axhline(41.5, color='white');ax.set_title(analysis['mode']+' / 마지막 B 실제각 RMS\n0~41 목표궤적,42~83 출력편향; 흰색=실패/미완료(84행 유지)')
    fig.colorbar(im, ax=ax, label='RMS 오차(°)');fig.tight_layout()
    path=root/('analysis_'+analysis['mode']+'_B.png');fig.savefig(path,dpi=160);plt.close(fig);output.append(str(path))
    return output


def number(x):
    return '미관측' if x is None else f'{x:.3f}'


def write_results(root, results):
    lines=['# 관절 제어 행렬 분석', '', '기타 조건: '+str(next(iter(results.values()))['guitar'])+'.', '', '현재 저장된 실제 GPU 진단 자료의 CPU 분석이다. 새 학습·재시뮬레이션은 수행하지 않았다.', '',
        '각 모드는21관절×양방향×2프로토콜=84행이다. 실패가 발생한 표본부터 제외하며, 미완료 구간을 통과로 세지 않는다. 동일 행·동일 명목 목표각 비교와 동일 출력값의 의미 차이 비교를 구분한다.', '',
        '| 모드 | 실패/84 | 추종 완료 창/84 | 완료 창 중 p95≤10° | B 완료 행/84 | B 통과 손가락 검사/336 | 최대 목표속도(rad/s) |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for mode, analysis in results.items():
        s=analysis['summary'];lines.append(f"| {mode} | {s['failed_cases']} | {s['tracking_windows_complete']} | {s['tracking_windows_complete_p95_le_10deg']} | {s['B_rows_complete']} | {s['B_checks_pass']} | {s['maximum_target_speed_rad_s']:.6f} |")
    lines += ['', '추종 창은 목표궤적42행의3~4초 및5.5~6초다. 240Hz 끝점 포함 표본의 선택 관절 |실제−목표| p95를 계산한다. 이 기준은 공학 진단 기준이며 무접촉을 인증하지 않는다. B는11.5~12초의60Hz31프레임×4축을 손가락마다 합쳐 RMS≤10°·최대≤20°인지 검사한다. 엄지는 B에서 제외한다.', '',
        '## 관절별 추종', '', '| 모드 | 행 | 관절 | 부호 | 3~4초 p95(°) | 5.5~6초 p95(°) | 두 창 완전관측 |', '| --- | ---: | --- | ---: | ---: | ---: | --- |']
    for mode, analysis in results.items():
        for row in analysis['rows']:
            if row['protocol']!='target_path':continue
            p,r=(row['tracking_windows'][k] for k in ('positive_hold','reverse_hold'))
            lines.append(f"| {mode} | {row['row']} | {row['joint']} | {row['sign']:+} | {number(p['p95'])} | {number(r['p95'])} | {p['fully_observed'] and r['fully_observed']} |")
    lines += ['', '## 지속 출력 편향', '', '1~6초에 같은 부호의0.05를 입력했다. incremental에서는 unclamped1rad(약57.296°)의 누적 요청이고, position에서는 초기 참조와 부호별 native 범위에 의해 정해지는 고정 목표각이다. 동일 행동값은 동일한 물리 입력이 아니다.', '',
        '| 모드 | 행 | 관절 | 부호 | 목표각 변화(°) | 실제각 변화(°) | 완전관측 |', '| --- | ---: | --- | ---: | ---: | ---: | --- |']
    for mode, analysis in results.items():
        for row in analysis['rows']:
            if row['protocol']!='output_bias':continue
            b=row['bias_forward'];lines.append(f"| {mode} | {row['row']} | {row['joint']} | {row['sign']:+} | {number(b['target_change_deg'])} | {number(b['actual_change_deg'])} | {b['fully_observed']} |")
    lines += ['', '## 초안 판단과 해석 한계', '']
    for mode, analysis in results.items():
        s=analysis['summary'];lines.append(f"- {mode}: 계획84개 추종 창 중 완전 관측{s['tracking_windows_complete']}개, 그중 p95≤10°는{s['tracking_windows_complete_p95_le_10deg']}개다. B 검사336개 중 완전 관측과 각도 기준을 함께 만족한 것은{s['B_checks_pass']}개다. 실패한 행도 전체 분모에 남겼다.")
    lines += ['', '이 비교는 스크립트 목표 제어의 응답이며 학습 정책의 자연스러움·음악 성공·두 제어 방식의 학습 성능 비교가 아니다. raw0은 누적 제어에서 목표 유지, 위치 제어에서 준비 참조 목표 복귀이므로 별도 분석했다. 목표각 한계 체류와 실제각 한계 체류는 JSON에서 분리했으며 native 경계1e−6rad와 공학 근접1°를 같은 항목으로 세지 않는다. 60Hz 전손 관절 지표와240Hz 선택 관절 지표도 구분한다.', '',
        '순힘 크기는 접촉 상대나 무접촉을 인증하지 않는다. 제출 effort_selected가0이어도 native POSITION drive의 실제 토크가0이라는 뜻이 아니다. 실제 모터 토크·effort 포화는 이 로그에서 측정하지 않았다. body_state는 환경0만 저장돼 다른83행의 충돌·몸체 자세를 이 배열로 주장할 수 없다. 실행기의 hard-failure 조건은 기타 변위/회전·속도·지지 방향 검사이며 전체 학습 종료 조건과 같다고 간주하지 않는다.', '',
        '표본을 잃은 구간은 available-sample 수치와 complete 여부를 함께 확인한다. 240Hz 체류시간은 유효 표본 수/240의 이산 지표이며 보간한 연속 접촉 시간이 아니다. 상세값과 입력 SHA는 `analysis.json`, 행별 요약은 `analysis.csv`에 있다.']
    lines += ['', '## 실제 수치에 근거한 해석', '']
    for mode, result in results.items():
        initial = max(r['initial_hold240']['selected_tracking_abs_deg']['p95'] for r in result['rows'])
        complete = [r for r in result['rows'] if r['B_final60']['fully_observed']]
        worst_b = max((v['actual_max_abs_deg'] for r in complete for v in r['B_final60']['fingers'].values()), default=None)
        worst_rms = max((v['actual_rms_deg'] for r in complete for v in r['B_final60']['fingers'].values()), default=None)
        paths = [r for r in result['rows'] if r['protocol']=='target_path']
        biases = [r for r in result['rows'] if r['protocol']=='output_bias']
        lines.append(f"- {mode}: 첫1초 선택축 추종오차 p95의 행별 최대는{initial:.3f}°다. 목표궤적 실패{sum(r['failure'] is not None for r in paths)}/42, 편향실험 실패{sum(r['failure'] is not None for r in biases)}/42다. 마지막 B창 완전관측은{len(complete)}/84행이며 그 행들의 손가락별4축 RMS 최대는{number(worst_rms)}°, 관절 최대 절대오차는{number(worst_b)}°다. 미관측 행을 빼고 전체 B 도달률을 주장하지 않는다.")
    paired = [(a,b) for a,b in zip(results['incremental']['rows'],results['position']['rows'])
              if a['protocol']=='output_bias' and a['bias_forward']['fully_observed'] and b['bias_forward']['fully_observed']]
    if paired:
        medians = [float(np.median([abs(p[i]['bias_forward']['target_change_deg']) for p in paired])) for i in (0,1)]
        lines.append(f"- 같은 양모드 완료 편향행{len(paired)}/42에서 목표각 변화 절댓값 중앙값은 누적{medians[0]:.3f}°, 위치{medians[1]:.3f}°다. 작은 지속 출력이 누적 제어에서 큰 각도 요청으로 변하는 구조를 확인한다. 두 모드의 동일0.05는 서로 다른 물리 입력이므로 학습 우열의 증거로 쓰지 않는다.")
    lines += ['- 완전관측된 작은 목표궤적의 추종이 양호하더라도, 접촉 부하·큰 편향·여러 손가락의 B 동시 이동에서 기타가 이탈한 원인은 별도로 봐야 한다. B 미완료만으로 B 각도 자체가 도달 불가능하다고 결론 내리지 않는다. 자유/고정 대조와 관절 추종을 함께 해석한다.',
              '- native 범위1e−6rad 초과 여부는 엄격 수치 진단이고1° 근접 체류와 다르다. 미세한 물리 범위 초과가 있으면 그 크기를 기록하되 이를 큰 관절 발산이나 코드의 목표각 범위 위반으로 확대하지 않는다.']
    (root/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args();root=args.root.resolve()
    results={};inputs={};figures=[]
    loaded={mode:load_run(root,mode) for mode in MODES}
    if loaded['incremental']['settings']['cases'] != loaded['position']['settings']['cases']:
        raise ValueError('Predeclared cases differ across modes')
    for key in ('joint_names','native_lower','native_upper','B_target_rad'):
        if loaded['incremental']['report'][key] != loaded['position']['report'][key]:
            raise ValueError('Controller reference/limits differ across modes: '+key)
    for mode in MODES:
        data=loaded[mode];results[mode]=analyze(data)
        figures.extend(plots(root,data,results[mode]))
        for name in ('settings.json','report.json','trace60.npz','trace240.npz','inputs_before.json'):
            path=data['run']/name;inputs[str(path)]=digest(path)
    if [r['joint'] for r in results['incremental']['rows']] != [r['joint'] for r in results['position']['rows']]:
        raise ValueError('Modes do not have aligned predeclared cases')
    inputs[str(Path(__file__).resolve())]=digest(Path(__file__).resolve())
    payload=dict(schema='guitar_learning.control_matrix_analysis.v1',input_sha256=inputs,
        sample_scope='failure-time sample excluded; tracking240Hz inclusive windows; B60Hz31frames; t0 excluded from limit occupancy',
        results=results,figures=figures,training_updates=0)
    (root/'analysis.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    fields=['mode','row','protocol','joint','sign','accepted_physics_samples','failure_time_s',
            'positive_hold_p95_deg','reverse_hold_p95_deg','bias_target_change_deg','bias_actual_change_deg',
            'raw_zero_target_change_deg','raw_zero_actual_change_deg','B_fingers_pass']
    with (root/'analysis.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for mode,result in results.items():
            for row in result['rows']:
                flat={k:row[k] for k in ('row','protocol','joint','sign','accepted_physics_samples')};flat['mode']=mode
                flat['failure_time_s']=row['failure']['time_s'] if row['failure'] else None
                for label in ('positive_hold','reverse_hold'):
                    flat[label+'_p95_deg']=row['tracking_windows'].get(label,{}).get('p95')
                for kind in ('target','actual'):
                    flat['bias_'+kind+'_change_deg']=row.get('bias_forward',{}).get(kind+'_change_deg')
                    flat['raw_zero_'+kind+'_change_deg']=row['raw_zero'][kind+'_change_deg']
                flat['B_fingers_pass']=sum(v['diagnostic_pass'] for v in row['B_final60']['fingers'].values())
                writer.writerow(flat)
    write_results(root,results)
    print(json.dumps({mode:result['summary'] for mode,result in results.items()},indent=2))


if __name__=='__main__':
    main()
