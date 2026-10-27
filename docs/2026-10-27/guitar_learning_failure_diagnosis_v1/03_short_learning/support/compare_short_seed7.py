"""Compare the two completed seed7 pilots using existing CPU artifacts only."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np


def read(path):
    return json.loads(path.read_text())


def main():
    base = Path(__file__).resolve().parents[1]
    folders = dict(incremental=base/'pilot_incremental_seed7_v2_retry2',
                   position=base/'pilot_position_seed7_v2')
    output = base/'comparison_seed7'
    output.mkdir(exist_ok=False)
    data, drift, settings, pins = {}, {}, {}, {}
    for mode, folder in folders.items():
        assert read(folder/'comparison_completed.json')['completed']
        assert read(folder/'analysis/summary_verification.json')['all_closed_verified']
        data[mode] = read(folder/'analysis/analysis.json')
        drift[mode] = read(folder/'analysis/policy_drift.json')
        settings[mode] = read(folder/'train/settings.json')
        for name in ('analysis/analysis.json', 'analysis/policy_drift.json',
                     'analysis/summary_verification.json', 'train/settings.json',
                     'evaluation_initial_reference/trace_env0_episode0.npz',
                     'evaluation_initial_reference/trace_metadata.json'):
            path = folder/name
            pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    differences = []

    def compare(a, b, path=''):
        if isinstance(a, dict) and isinstance(b, dict):
            assert a.keys() == b.keys()
            for key in sorted(a):
                compare(a[key], b[key], path+'/'+key)
        elif a != b:
            differences.append(dict(path=path, incremental=a, position=b))

    compare(settings['incremental'], settings['position'])
    assert {d['path'] for d in differences} == {
        '/initial_std', '/song/finger_action_mode',
        '/song/short_learning/initial_std', '/song/short_learning/mode'}
    traces = {m: np.load(f/'evaluation_initial_reference/trace_env0_episode0.npz')
              for m, f in folders.items()}
    meta = read(folders['position']/'evaluation_initial_reference/trace_metadata.json')
    names = drift['position']['selected_joint_names']
    indices = [meta['joint_names'].index(n) for n in names]
    reference_difference = dict(scope='prespecified env0 first reference attempt; not all128 trajectories')
    for key in ('target', 'q'):
        delta = np.degrees(np.abs(traces['incremental'][key][:, indices] -
                                  traces['position'][key][:, indices]))
        reference_difference[key+'_selected_max_difference_deg'] = float(delta.max())
        reference_difference[key+'_selected_first60_max_difference_deg'] = float(delta[:60].max())
    reference_difference['wrist_arm_request_max_difference_deg'] = float(np.degrees(np.abs(
        traces['incremental']['wrist_requested_arm_rad'] - traces['position']['wrist_requested_arm_rad'])).max())
    result = dict(schema='short_comparison_seed7.v1', settings_differences=differences,
        source_inputs_sha256=pins, evaluations={m:d['evaluations'] for m,d in data.items()},
        reference_env0_difference=reference_difference,
        pass_criteria=dict(achievement=.8, clean=.7, wrong_max=.1, physical_failure_max=.05,
                           consecutive_evaluations=2),
        passed=dict(incremental=False, position=False))
    (output/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    font = FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family'] = font.get_name()
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2,2,figsize=(13,9))
    x = [0,50,100,150,200,250,300]
    labels = dict(incremental='증분 제어', position='위치 제어')
    for mode in folders:
        rows = drift[mode]['checkpoints']
        axes[0,0].plot(x,[r['summary']['achieved_fraction'] for r in rows],marker='o',label=labels[mode])
        axes[0,1].plot(x,[r['summary']['mean_audible_wrong_fraction'] for r in rows],marker='o',label=labels[mode])
        offset = -.2 if mode=='incremental' else .2
        angles = rows[-1]['selected_angles_all128']
        axes[1,0].bar(np.arange(4)+offset, angles['actual_range_deg']['median'],.38,label=labels[mode])
        axes[1,1].bar(np.arange(4)+offset, angles['target_native_limit_fraction']['mean'],.38,label=labels[mode])
    for ax,title in zip(axes[0],('압현 달성률 · 각128시도','음 구간 오압현 비율 · 각128시도')):
        ax.set_title(title);ax.set_ylim(-.03,1.03);ax.set_xlabel('학습 업데이트')
    axes[0,0].axhline(.8,color='gray',ls='--',label='통과 목표80%')
    axes[0,1].axhline(.1,color='gray',ls='--',label='통과 상한10%')
    axes[1,0].set_title('최종 실제각 범위 · 128시도 중앙값');axes[1,0].set_ylabel('도(°)')
    axes[1,1].set_title('최종 명령 한계 체류 · 128시도 평균');axes[1,1].set_ylim(0,1)
    for ax in axes[1]:
        ax.set_xticks(np.arange(4));ax.set_xticklabels([n.replace('LH:','') for n in names])
    for ax in axes.flat:
        ax.grid(axis='y',alpha=.2);ax.legend(fontsize=9)
    fig.suptitle('seed7 · 고정 기타/중지1음/teacher 팔 · 제어 우열 일반화 불가')
    fig.tight_layout();fig.savefig(output/'comparison.png',dpi=140);plt.close(fig)
    lines = ['# seed7: 증분·위치 제어 300회 비교','',
        '두 방식 모두 계획한 통과 기준에 미달했다. 증분 제어는 50회 정책에서 압현을 학습했지만 이후 후퇴했고, 위치 제어는 이번 조건에서 압현이 발생하지 않았다.', '',
        '같은 large·128환경·H32·K1·300회·seed7, 원곡 중지 한 음, 2초 유한 손목 teacher 및 다른 손가락 B를 사용했다. 시작부터 준비 구간도 학습했다. 설정 차이는 제어 방식과 사전 교정 std 두 항목뿐이며, 각 항목의 상위/하위 기록을 합쳐4개 키다. 기본 학습 소스와 입력은 바꾸지 않았다.', '',
        '한 tick 목표각 변화의 RMS를 맞춘 std(.171171/.01)는 장기간 누적 탐색이나 실제 물리 응답을 같게 하지 않는다. 따라서 결과를 제어 방식의 일반적 우열로 해석하지 않는다.', '',
        '| 정책 시점 | 증분 달성/128 | 위치 달성/128 | 증분 clean | 위치 clean | 증분 wrong | 위치 wrong |',
        '|---:|---:|---:|---:|---:|---:|---:|']
    for a,b in zip(drift['incremental']['checkpoints'],drift['position']['checkpoints']):
        sa,sb=a['summary'],b['summary']
        lines.append('| %d | %d | %d | %.3f | %.3f | %.3f | %.3f |'%(
            a['update'],round(128*sa['achieved_fraction']),round(128*sb['achieved_fraction']),
            sa['mean_clean_fraction'],sb['mean_clean_fraction'],sa['mean_audible_wrong_fraction'],sb['mean_audible_wrong_fraction']))
    lines += ['', '각 행은128환경의 첫 시도 전부다. 학습 각각5,632 완료 에피소드와 평가 각1,280시도에서 물리·손목 종료는0이었다. 최고 저장 정책인 증분50회도 달성66.41%·clean66.30%로 기준80%·70%에 못 미친다. 연속 두 평가 통과 조건도 충족하지 않는다.', '',
        '| 대조 | 증분 달성/128 | 위치 달성/128 |','|---|---:|---:|']
    for condition in ('policy','zero','random','reference'):
        values=[data[m]['evaluations']['evaluation_initial_'+condition] for m in folders]
        lines.append('| 초기 %s | %d | %d |'%(condition,round(values[0]['achieved_fraction']*128),round(values[1]['achieved_fraction']*128)))
    lines += ['',
        'Script reference는 손가락까지 정해진 동작으로 제어한 도달 대조이며 정책 학습 성과가 아니다. 증분 reference의 clean/wrong은85.12%/14.13%, 위치는58.76%/32.00%다. 둘 다 완벽하지 않다. 사전 지정env0의 선정4축 목표각 차이는 최대8.54e−7°이나 실제각은2.516°, 손목 feedback 팔 요청은9.33° 차이가 났다. 작은 초기 차이 이후 실제 물리가 분기한 관측이며 원인을 확정하지 않는다. 상세 비교는 comparison.json에 있다.', '',
        '증분 std는 약.171, 위치는 약.01로 거의 유지됐다. 증분 최종은 준비 중 큰 누적 움직임과 명령 한계 체류, 위치 최종은 선정4축 실제 움직임 범위 중앙값 약1.5~2.95°와 한계 체류0을 보였다. 둘 다 단순한 제어 정지로 설명되지 않는다. 평균 출력과 std 전체는 두 실행의 analysis/policy_drift.json에 있다.', '',
        '증분50회 에피소드 보상+.75780보다 최종−.03625가 낮고, 위치도 초기−.19323에서 최종−.20927로 개선되지 않았다. 보상 수식의 즉시 점수만으로 학습 후퇴의 원인을 확정하지 않는다. 저장된 checkpoint의 갱신 방향·가치 추정·시간축 보상 전달을 점검할 자료를 인계했다. 새seed17 학습은 하지 않았다.', '',
        '이 결과는 고정 기타·한 목표·한 seed·teacher 조건에 한정된다. 자유 기타나 곡 단위 성공, 네 손가락 전체 성능을 의미하지 않는다. 이전 증분 retry1은 호스트 재부팅으로 중단돼 원자료를 보존했고, 동일 조건 fresh retry2에서 수행했다.', '',
        '![두 제어 방식 비교](comparison.png)', '']
    (output/'RESULTS.md').write_text('\n'.join(lines))
    print(output)


if __name__=='__main__':
    main()
