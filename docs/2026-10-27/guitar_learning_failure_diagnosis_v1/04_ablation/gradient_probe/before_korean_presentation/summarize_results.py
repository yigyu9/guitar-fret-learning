"""CPU summary and plots of the three predeclared frozen probes."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch

from probe_math import decompose
from guitar_learning.training.ppo import PPOConfig


BASE = Path(__file__).resolve().parents[1]
LABELS = ['Approach', 'First contact', 'Clean hold', 'Achievement', 'Wrong press',
          'Deficit', 'Standby', 'Thumb', 'Action change', 'Reward value residual', 'Negative cost GAE']


def read(path):
    return json.loads(path.read_text())


def main():
    torch.set_num_threads(1)
    results, all_inputs = [], {}
    for cp in (50,100,300):
        folder = BASE/('probe_cp%d_v1'%cp)
        report, invocation = read(folder/'report.json'), read(folder/'invocation.json')
        before, after = read(folder/'inputs_before.json'), read(folder/'inputs_after.json')
        if not (report['completed'] and report['scene_closed'] and report['model_unchanged']
                and report['checkpoint_unchanged'] and report['lifecycle_verified']
                and report['optimizer_steps']==0 and after['verified'] and before==after['input_pins']):
            raise AssertionError('Probe report failed')
        if any(path in all_inputs and all_inputs[path]!=value for path,value in before.items()):
            raise AssertionError('Inputs differ across frozen probes')
        all_inputs.update(before)
        config=PPOConfig(**read(folder/'settings.json')['ppo'])
        batches=[]
        for batch in range(1,8):
            item=read(folder/('batch_%02d.json'%batch))
            with np.load(folder/('batch_%02d.npz'%batch)) as raw:
                a={key:raw[key].copy() for key in raw.files}
            if not all(np.isfinite(x).all() for x in a.values()):raise AssertionError('Nonfinite arrays')
            b={key:torch.from_numpy(a[key]) for key in ('reward','cost','reward_value','next_reward_value',
                'cost_value','next_cost_value','valid','duration','terminated','truncated')}
            recomputed=decompose(b,torch.from_numpy(a['reward_components']),config,config.cost_weight)
            for key in ('raw','normalized_pieces','reward_gae','cost_gae','combined','normalized'):
                np.testing.assert_allclose(recomputed[key].numpy(),a['advantage_'+key],atol=2e-6,rtol=2e-6)
            item.update(raw_cost_sum=float(a['cost'].sum()),raw_reward_sums=a['reward_components'].sum((0,1)).tolist(),
                mean_reward_value=float(a['reward_value'].mean()),mean_cost_value=float(a['cost_value'].mean()),
                local_time_range_s=[float(a['local_time_s'].min()),float(a['local_time_s'].max())],
                source_time_range_s=[float(a['source_time_s'].min()),float(a['source_time_s'].max())],
                independent_saved_GAE_recheck=True)
            batches.append(item)
        g=[x['gradients']['groups']['all'] for x in batches]
        episodes=[r for b in batches for r in b['episode_completions']]
        results.append(dict(checkpoint_updates=cp,report=report,invocation=invocation,batches=batches,
            summary=dict(fresh_completed_episodes=len(episodes),
                achieved_count=sum(r['achieved'] for r in episodes),
                clean_fraction_mean=float(np.mean([r['clean_fraction'] for r in episodes])) if episodes else None,
                wrong_fraction_mean=float(np.mean([r['audible_wrong_fraction'] for r in episodes])) if episodes else None,
                component_gradient_norm_mean=np.mean([x['component_norm'] for x in g],0).tolist(),
                negative_dot_batch_counts=(np.asarray([x['signed_dot_total'] for x in g])<0).sum(0).tolist(),
                total_gradient_norm_by_batch=[x['total_norm'] for x in g],raw_cost_sum=sum(b['raw_cost_sum'] for b in batches),
                max_gradient_sum_abs_error=max(b['gradients']['check']['max_abs'] for b in batches),
                max_gradient_sum_relative_l2_error=max(b['gradients']['check']['relative_l2'] for b in batches),
                max_ratio_error=max(b['gradients']['max_ratio_error'] for b in batches))))
    changed=[p for p,h in all_inputs.items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    if changed:raise AssertionError('Probe inputs changed: '+repr(changed))
    summary=dict(schema='frozen_gradient_probe_comparison.v1',completed=True,component_order=LABELS,
        source_input_count=len(all_inputs),source_inputs_currently_unchanged=True,checkpoints=results,
        scope='new stochastic frozen-policy rollout; separately normalized4096 batches; no historical gradient reproduction or causal performance percentages',
        models_and_checkpoints_unchanged=True,optimizer_steps=0,gpu_released=True)
    (BASE/'comparison.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    for metric,name,title in [('component_norm','gradient_norm_heatmaps.png','Gradient norm (log10; before clipping and Adam)'),
                              ('cosine_total','gradient_alignment_heatmaps.png','Cosine with total first gradient (local batch alignment)')]:
        fig,axes=plt.subplots(1,3,figsize=(18,6),sharey=True)
        fig.subplots_adjust(left=.16,right=.92,wspace=.06,bottom=.14,top=.82)
        values=[]
        for r in results:
            a=np.asarray([b['gradients']['groups']['all'][metric] for b in r['batches']],dtype=float).T
            values.append(np.log10(np.maximum(a,1e-12)) if metric=='component_norm' else a)
        limits=(min(x.min() for x in values),max(x.max() for x in values)) if metric=='component_norm' else (-1,1)
        cmap=plt.get_cmap('viridis' if metric=='component_norm' else 'RdBu_r').copy()
        cmap.set_bad('#dedede')
        for ax,r,a in zip(axes,results,values):
            im=ax.imshow(a,aspect='auto',vmin=limits[0],vmax=limits[1],cmap=cmap)
            ax.set_title('Checkpoint %d'%r['checkpoint_updates']);ax.set_xticks(range(7),range(1,8));ax.set_xlabel('Independent H32 batch')
            ax.set_yticks(range(11),LABELS);ax.axvline(4.5,color='white',lw=1,ls='--')
        cax=fig.add_axes([.94,.18,.014,.60])
        fig.colorbar(im,cax=cax,label='log10 norm (zero displayed at -12)' if metric=='component_norm' else 'cosine')
        fig.suptitle(title+'\n7 consecutive batches; batches6/7 include audible/ending-reset context')
        fig.savefig(BASE/name,dpi=160);plt.close(fig)
    lines=['# Frozen 정책의 첫 기울기 측정 결과','',
        '체크포인트50·100·300의 실제 GPU 진단을 각각 완료했다. 세 모델 모두 고정 상태에서224틱(896물리step),128환경을 실행했으며 소스·체크포인트·모델 불변성과 scene 종료를 통과했다. 각32틱 배치를 따로 정규화했다. 새 학습이나 optimizer 갱신은 수행하지 않았다.','',
        '| 체크포인트 | 새 완료 에피소드 / 달성 | clean 평균 | wrong 평균 | 기울기 합 최대오차 | raw cost 합 |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in results:
        s=r['summary'];lines.append('| %d | %d / %d | %.4f | %.4f | %.3g | %.3g |'%(r['checkpoint_updates'],s['fresh_completed_episodes'],s['achieved_count'],s['clean_fraction_mean'],s['wrong_fraction_mean'],s['max_gradient_sum_abs_error'],s['raw_cost_sum']))
    lines += ['', '위 에피소드 값은 이 **확률적 frozen rollout**의 부수 결과이며 별도 deterministic10회 평가와 동일한 표본이 아니다. 동일 seed도 서로 다른 정책의 궤적을 같게 만들지 않는다.','',
        '세 모델 모두7배치 평균 norm은 reward value residual이 가장 컸다. cp300은 최초 접촉·압현 유지·달성·오압현 성분의 gradient가 모두0인 반면, 대기 자세·엄지 안내·critic residual은 남았다. 이 새 rollout에서 올바른 접촉까지 이르는 표본과 그 직접 보상 신호가 사라졌다는 관측이며, 대기/엄지/critic이 퇴행을 일으켰다는 인과 증거는 아니다.','',
        '| 성분 | cp50 평균 norm | cp100 평균 norm | cp300 평균 norm |',
        '| --- | ---: | ---: | ---: |']
    for i,label in enumerate(LABELS):
        lines.append('| %s | %.4g | %.4g | %.4g |'%(label,*(r['summary']['component_gradient_norm_mean'][i] for r in results)))
    lines += ['',
        '![성분별 기울기 크기](gradient_norm_heatmaps.png)','',
        '![전체 기울기와의 방향 정렬](gradient_alignment_heatmaps.png)','',
        '행별 크기는 공유 전체 actor 파라미터에 대한 clipping·Adam 이전의 norm이다. 양의 cosine은 해당 성분의 손실 기울기가 전체 손실 기울기와 같은 방향이고, 음수는 반대 방향이라는 뜻이다. 회색은 성분 norm이0에 가까워 cosine을 정의하지 않은 칸이다. gradient descent는 이 벡터의 음의 방향으로 움직인다. 성능의 인과적 기여율이나 최종 parameter 변화의 정확한 분해로 해석하지 않는다.','',
        '보상9항에 value baseline을 임의 분배하지 않고 reward critic residual을10번째로 분리했다. 마지막은 원래 cost GAE 전체에 -cost_weight를 곱한 성분이다. raw cost가0이어도 학습된 critic이0이 아니면 마지막 성분은0이 아닐 수 있다. 이는 이 고정 모델과 새 배치에서의 수치적 현상이며 회귀의 원인이라는 증거는 아니다.','',
        '배치6은 원래 음 시점, 배치7은 말미·자연 종료와 다음 에피소드 초반을 포함한다. 초기 실패가 있으면 실제 종료·리셋이 그대로 반영된다. 배치별 원본 시간·episode ID·terminal/truncation과 실제 완료 에피소드를 보존했다. 저장된 보상·값에서 GAE와 정규화 성분을 CPU로 다시 계산해 전부 일치했다.','',
        '[기계 판독 비교](comparison.json) · [구현·실행 계약](README.md)']
    (BASE/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    files=[BASE/'comparison.json',BASE/'RESULTS.md',BASE/'gradient_norm_heatmaps.png',BASE/'gradient_alignment_heatmaps.png',Path(__file__).resolve()]
    for cp in (50,100,300):
        folder=BASE/('probe_cp%d_v1'%cp)
        files.extend(sorted(folder.glob('*.json')))
        files.extend(sorted(folder.glob('*.npz')))
    verification=dict(completed=True,all_three_reports_completed=True,all_three_scenes_closed=True,
        all_three_model_checkpoint_source_unchanged=True,independent_saved_GAE_rechecks=21,source_input_count=len(all_inputs),changed_inputs=changed,
        artifact_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (BASE/'gpu_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps([dict(cp=r['checkpoint_updates'],**r['summary']) for r in results],indent=2))


if __name__=='__main__':main()
