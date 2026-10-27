"""CPU-only comparison of completed seed7/17 pilots; no new evaluation."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import torch


def read(path):
    return json.loads(path.read_text())


def main():
    base = Path(__file__).resolve().parents[1]
    output = base/'comparison_seed7_seed17'
    runs, pins = {}, {}
    updates = [0,50,100,150,200,250,300]
    for mode in ('incremental','position'):
        for seed in (7,17):
            name = '%s_seed%d' % (mode, seed)
            suffix = '_retry2' if mode=='incremental' and seed==7 else ''
            folder = base/('pilot_'+name+'_v2'+suffix)
            assert read(folder/'comparison_completed.json')['completed']
            assert read(folder/'analysis/summary_verification.json')['all_closed_verified']
            settings = read(folder/'train/settings.json')
            spec = settings['song']['short_learning']
            assert settings['seed']==seed and spec['mode']==mode and spec['finger']==2
            episodes = [json.loads(line) for line in (folder/'train/episodes.jsonl').read_text().splitlines()]
            checkpoints = []
            for update in updates:
                evaluation_folder = folder/('evaluation_initial_policy' if update==0 else 'evaluation_%06d'%update)
                evaluation = read(evaluation_folder/'evaluation.json')
                attempts = evaluation['episodes']
                assert len(attempts)==128 and sorted(x['env_id'] for x in attempts)==list(range(128))
                checkpoint = folder/'train'/('initial.pt' if update==0 else 'final.pt' if update==300 else 'evaluation_%06d.pt'%update)
                model = torch.load(checkpoint,map_location='cpu',weights_only=False)['model']
                logstd = model['finger_log_std'][4:8].double().numpy()
                names = attempts[0]['angles']['joint_names']
                indices = [names.index(n) for n in spec['learned_action_names']]
                angles = {}
                for key in ('actual_range_rad','actual_native_limit_fraction','target_native_limit_fraction'):
                    array = np.asarray([x['angles']['values'][key] for x in attempts])[:,indices]
                    if key=='actual_range_rad': array=np.degrees(array)
                    angles[key.replace('_rad','_deg')] = dict(mean=array.mean(0).tolist(),median=np.median(array,axis=0).tolist())
                summary = evaluation['summary']
                passed = summary['achieved_fraction']>=.8 and summary['mean_clean_fraction']>=.7 and summary['mean_audible_wrong_fraction']<=.1 and summary['physical_failure_fraction']<=.05
                checkpoints.append(dict(update=update,summary=summary,single_pass=passed,
                    raw_logstd=logstd.tolist(),effective_std=np.exp(np.clip(logstd,-5,2)).tolist(),
                    selected_angles=angles,mean_total_reward=float(np.mean([x['reward'] for x in attempts]))))
                for path in (checkpoint,evaluation_folder/'evaluation.json'):
                    pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
            controls = {control:read(folder/('evaluation_initial_'+control)/'evaluation.json')['summary']
                        for control in ('policy','zero','random','reference')}
            for control in controls:
                path=folder/('evaluation_initial_'+control)/'evaluation.json'
                pins[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
            windows = []
            for end in (50,100,150,200,250,300):
                rows = [x for x in episodes if end-50<x['update']<=end]
                windows.append(dict(end_update=end,episodes=len(rows),achieved=sum(x['achieved'] for x in rows),
                    achieved_fraction=sum(x['achieved'] for x in rows)/len(rows)))
            passes = [x['update'] for x in checkpoints if x['single_pass']]
            runs[name] = dict(mode=mode,seed=seed,settings=settings,checkpoints=checkpoints,
                passing_updates=passes,consecutive_two_pass=any(u+50 in passes for u in passes),
                controls=controls,training_windows=windows,training_episodes=len(episodes),
                training_achieved=sum(x['achieved'] for x in episodes),
                training_failures=sum(x['termination']['physical_failure'] or x['termination']['wrist_failure'] for x in episodes))
            for name in ('train/settings.json','train/inputs_before.json','train/inputs_after.json','train/report.json',
                         'train/episodes.jsonl','analysis/summary_verification.json','comparison_completed.json'):
                path=folder/name;pins[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    assert not torch.cuda.is_initialized()
    pins[str(Path(__file__).resolve())] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output.mkdir(exist_ok=False)
    result = dict(schema='short_replications.v1',runs=runs,input_sha256=pins,
        selected_joint_names=spec['learned_action_names'],
        scopes=dict(training='stochastic rollout episodes completed within update bins; policies change within bins',
            evaluation='deterministic mean policy;128 assigned first attempts including failures',
            std='latent Gaussian before tanh; clamp[-5,2]; not joint-displacement std',
            angles='all128 first attempts,60Hz endpoints,native tolerance1e-6rad; actual ranges in degrees'),
        criteria=dict(achievement_min=.8,clean_min=.7,wrong_max=.1,physical_failure_max=.05,consecutive_evaluations=2))
    (output/'comparison.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family']=font.get_name();plt.rcParams['axes.unicode_minus']=False
    fig,axes=plt.subplots(2,2,figsize=(13,9))
    for name,run in runs.items():
        label=('증분' if run['mode']=='incremental' else '위치')+' seed%d'%run['seed']
        style='-' if run['seed']==7 else '--';color='tab:blue' if run['mode']=='incremental' else 'tab:orange'
        for ax,key in zip(axes.flat[:3],('achieved_fraction','mean_clean_fraction','mean_audible_wrong_fraction')):
            ax.plot(updates,[c['summary'][key] for c in run['checkpoints']],style,marker='o',color=color,label=label)
        axes[1,1].plot([w['end_update'] for w in run['training_windows']],
            [w['achieved_fraction'] for w in run['training_windows']],style,marker='o',color=color,label=label)
    titles=('결정론 평가 달성률 · 각128시도','결정론 평가 clean · 각128시도',
            '결정론 평가 오압현 · 각128시도','확률적 훈련 달성률 · 50회 내 완료시도')
    for ax,title in zip(axes.flat,titles):
        ax.set_title(title);ax.set_xlabel('학습 업데이트');ax.set_ylim(-.03,1.03);ax.grid(alpha=.2);ax.legend(fontsize=9)
    for ax,value in zip(axes.flat[:3],(.8,.7,.1)):ax.axhline(value,color='gray',ls=':',lw=1)
    fig.suptitle('고정 기타·중지1음·teacher 팔 · 훈련과 고정 정책 평가 구분')
    fig.tight_layout();fig.savefig(output/'comparison.png',dpi=140);plt.close(fig)
    lines=['# seed7/17 고정 과제 반복 비교','',
        '각 실행은 large·128환경·H32·K1·300회, 동일 원곡 중지 한 음·고정 기타·2초 유한 손목 teacher·나머지 손가락 B 조건이다. 제어 방식별 사전 교정 std는 증분.1711710545, 위치.01이며 보상·물리·입력·학습 코드를 변경하지 않았다.','',
        '**훈련은 확률적 행동 수집, 평가는 결정론적 평균 정책이다.** 훈련 표는50회 동안 서로 다른 갱신 시점에 완료된 에피소드이므로, 저장된 단일 정책의128시도 평가와 같은 표본으로 취급하지 않는다.','',
        '| 조건 | 초기/50/100/150/200/250/300 달성(각128) | 단일 기준 충족 | 연속2회 통과 |','|---|---|---|---|']
    for name,run in runs.items():
        counts=[round(128*c['summary']['achieved_fraction']) for c in run['checkpoints']]
        lines.append('| %s | %s | %s | %s |'%(name,' / '.join(map(str,counts)),str(run['passing_updates']),str(run['consecutive_two_pass'])))
    lines += ['', '단일 기준은 달성≥80%, clean≥70%, wrong≤10%, 물리 실패≤5%이며 사전 지정한 연속 두 평가를 요구한다. 실패 시도를 분모에서 제외하지 않는다.','',
        '| 조건 | 훈련 달성/완료 | 최종 latent std 4축 | 최종 실제각 범위 중앙값4축(°) |','|---|---:|---|---|']
    for name,run in runs.items():
        final=run['checkpoints'][-1]
        lines.append('| %s | %d/%d | %s | %s |'%(name,run['training_achieved'],run['training_episodes'],
            ', '.join('%.6f'%v for v in final['effective_std']),
            ', '.join('%.3f'%v for v in final['selected_angles']['actual_range_deg']['median'])))
    lines += ['', '4축 순서는 middle1_x, middle1_z, middle2, middle3이다. std는tanh 이전 Gaussian이며 각도 변화량이 아니다. 실제/명령 native 한계 체류는 comparison.json에 별도로 저장했다.','',
        '| 조건 | 초기policy / zero / random / reference 달성(각128) | reference clean / wrong |','|---|---|---|']
    for name,run in runs.items():
        controls=run['controls'];ref=controls['reference']
        lines.append('| %s | %s | %.4f / %.4f |'%(name,' / '.join(str(round(128*controls[k]['achieved_fraction'])) for k in ('policy','zero','random','reference')),ref['mean_clean_fraction'],ref['mean_audible_wrong_fraction']))
    lines += ['',
        'Script reference는 손가락도 정해진 동작으로 제어하는 도달 대조다. 정책 성과가 아니며, 두 제어 방식의 실제 물리 반응은 완전히 같지 않았다. 한tick 목표각 RMS 교정도 장기간 탐색·접촉 반응의 동등성을 보장하지 않는다.','',
        '증분seed17은150회127/128과최종128/128에 도달해 고정 과제의 압현 학습 가능성을 보였다. 그러나200회0/128,250회 오압현 증가와seed7최종0/128이 있어 성능 유지와seed 안정성은 미해결이다. 이번 관측만으로 제어 방식의 일반적인 우열이나 학습 후퇴의 단일 원인을 확정하지 않는다.','',
        '최종 압현100%는 손가락 움직임의 자연스러움이나 관절 한계 체류 문제의 해결을 증명하지 않는다. 실제각 범위와 한계 체류 통계는 준비를 포함한 전체 에피소드의60Hz 표본이며, 특정 음 구간의 움직임만 측정한 값이 아니다. 실제각과 명령각 한계 체류는 구분해서 읽어야 한다.','',
        '전체 곡·자유 기타·네 손가락 전체의 성과가 아니다. 정해진300회와10개 평가 외의 GPU 평가를 추가하지 않았다. 원자료와 입력 봉인은 각 실행 폴더에 보존했다.','',
        '![반복 비교](comparison.png)','']
    (output/'RESULTS.md').write_text('\n'.join(lines))
    print(output)


if __name__=='__main__':
    main()
