"""CPU-only sampled complete-episode MC calibration of frozen stored values."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


BASE=Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def statistics(prediction, observed):
    x,y=np.asarray(prediction,dtype=np.float64).ravel(),np.asarray(observed,dtype=np.float64).ravel()
    error=x-y
    variance_x,variance_y=float(x.var()),float(y.var())
    covariance=float(np.mean((x-x.mean())*(y-y.mean())))
    slope=covariance/variance_x if variance_x>1e-12 else None
    order=np.argsort(x,kind='stable')
    bins=[]
    for ids in np.array_split(order,5):
        bins.append(dict(samples=len(ids),prediction_mean=float(x[ids].mean()),observed_return_mean=float(y[ids].mean()),
            prediction_range=[float(x[ids].min()),float(x[ids].max())],observed_return_std=float(y[ids].std())))
    return dict(samples=len(x),mse=float(np.mean(error**2)),rmse=float(np.sqrt(np.mean(error**2))),
        mae=float(np.mean(np.abs(error))),bias_prediction_minus_observed=float(error.mean()),
        prediction_mean=float(x.mean()),prediction_std=float(x.std()),
        observed_return_mean=float(y.mean()),observed_return_std=float(y.std()),
        pearson_correlation=covariance/np.sqrt(variance_x*variance_y) if min(variance_x,variance_y)>1e-12 else None,
        regression_observed_on_prediction=dict(slope=slope,intercept=float(y.mean()-slope*x.mean()) if slope is not None else None),
        equal_count_prediction_bins=bins)


def main():
    paths=[Path(__file__).resolve()]
    for cp in (50,100,300):
        folder=BASE/('probe_cp%d_v1'%cp)
        paths.extend([folder/'settings.json',folder/'report.json',*sorted(folder.glob('batch_*.npz'))])
    before={str(p):sha(p) for p in paths}
    values,curves,returns={}, {}, {}
    recurrence_errors=[]
    for cp in (50,100,300):
        folder=BASE/('probe_cp%d_v1'%cp)
        settings=read(folder/'settings.json');report=read(folder/'report.json')
        assert report['completed'] and report['model_unchanged'] and report['scene_closed']
        arrays={}
        for batch in range(1,8):
            with np.load(folder/('batch_%02d.npz'%batch)) as a:
                for key in ('reward','cost','reward_value','cost_value','terminated','truncated','episode_id','local_time_s'):
                    arrays.setdefault(key,[]).append(a[key].copy())
        arrays={key:np.concatenate(parts) for key,parts in arrays.items()}
        done=arrays['terminated']|arrays['truncated']
        assert done.shape==(224,128) and np.all(arrays['episode_id'][:218]==0)
        assert not done[:217].any() and done[217].all() and not done[218:].any()
        assert np.all(arrays['episode_id'][218:]==1)
        if arrays['truncated'][:218].any():raise AssertionError('Complete terminal episodes required, not rollout truncation')
        local=arrays['local_time_s'][:218]-1/60
        np.testing.assert_allclose(local,np.arange(218)[:,None]/60+np.zeros((218,128)),atol=1e-10,rtol=0)
        view=settings['song']['short_learning']['view']
        onset,end=view['local_onset_s'],view['local_end_s']
        phases=dict(all=np.ones_like(local,dtype=bool),preparation=local<onset-1e-10,
            audible=(local>=onset-1e-10)&(local<end-1e-10),tail=local>=end-1e-10)
        cp_result=dict(complete_first_episodes=128,episode_ticks=218,discarded_second_episode_ticks=6,
            value_observation_time='stored control endpoint time minus1/60; before associated action/reward',
            phase_boundaries_local_s=dict(onset=onset,end=end),critics={})
        curves[cp]={'time':local[:,0],'onset':onset,'end':end}
        for kind,gamma in (('reward',settings['ppo']['gamma']),('cost',settings['ppo']['cost_gamma'])):
            reward=arrays[kind][:218].astype(np.float64)
            prediction=arrays[kind+'_value'][:218].astype(np.float64)
            observed=np.zeros_like(reward);carry=np.zeros(128)
            for t in reversed(range(218)):
                carry=reward[t]+gamma*(~done[t])*carry
                observed[t]=carry
            explicit=np.stack([(reward[t:]*gamma**np.arange(218-t)[:,None]).sum(0) for t in range(218)])
            np.testing.assert_allclose(observed,explicit,atol=2e-12,rtol=2e-12)
            np.testing.assert_array_equal(observed[-1],reward[-1])
            err=float(np.max(np.abs(observed-explicit)));recurrence_errors.append(err)
            cp_result['critics'][kind]=dict(gamma=gamma,bootstrap=False,
                recurrence_vs_explicit_discounted_sum_max_error=err,
                phases={name:statistics(prediction[mask],observed[mask]) for name,mask in phases.items()})
            curves[cp][kind]=dict(prediction_mean=prediction.mean(1),observed_mean=observed.mean(1),observed_std=observed.std(1))
            returns['cp%d_%s_MC_return'%(cp,kind)]=observed
        values[str(cp)]=cp_result
    changed=[p for p,h in before.items() if sha(Path(p))!=h]
    assert not changed
    result=dict(schema='frozen_value_sampled_MC_calibration.v1',completed=True,gpu_used=False,
        checkpoints=values,first_episode_only=True,complete_episodes_per_checkpoint=128,
        discount_scope='218tick actual complete episode, rewardgamma.99/costgamma1; no critic bootstrap; not a change to the separately normalized H32 gradient probe',
        return_target_scope='single sampled discounted return for each observed state; not the true expected value',
        residual_scope='reward-value GAE residual B_r is a baseline-related algebraic component, not itself prediction error; it may include legitimate baseline effects',
        no_causal_claim=True,sample_dependence='states share trajectories; quantile bins and correlations are descriptive, no independent-sample inference',
        correlation_null_when_constant=True,recurrence_max_abs_error=max(recurrence_errors))
    (BASE/'value_calibration.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    np.savez_compressed(BASE/'complete_episode_MC_returns.npz',**returns)
    plt.rcParams.update({'font.family':'NanumGothic','font.size':10,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(15,7),sharex=True)
    fig.subplots_adjust(left=.07,right=.99,top=.84,bottom=.08,wspace=.27,hspace=.38)
    for column,cp in enumerate((50,100,300)):
        for row,kind in enumerate(('reward','cost')):
            ax=axes[row,column];data=curves[cp][kind];time=curves[cp]['time']
            ax.plot(time,data['prediction_mean'],label='저장된 가치 예측 평균',color='#2865a8')
            ax.plot(time,data['observed_mean'],label='관측 완결 MC return 평균',color='#252525',ls='--')
            ax.fill_between(time,data['observed_mean']-data['observed_std'],data['observed_mean']+data['observed_std'],color='#777777',alpha=.15,label='관측 return ±표준편차')
            ax.axvspan(curves[cp]['onset'],curves[cp]['end'],color='#4b9d67',alpha=.15)
            ax.set_title('체크포인트 %d · %s'%(cp,'보상' if kind=='reward' else '비용'))
            ax.set_xlabel('행동 이전 로컬 시각(초)');ax.set_ylabel('가치 / 할인 관측 return');ax.grid(alpha=.15)
    axes[0,0].legend(loc='best',fontsize=8)
    fig.suptitle('고정 critic과 실제 완결 에피소드의 할인 return 비교\n초록 영역: 목표 음 구간 · 회색 폭은 표본 분산이며 신뢰구간이 아님')
    fig.savefig(BASE/'value_calibration_time_curves.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,3,figsize=(15,7))
    fig.subplots_adjust(left=.07,right=.99,top=.84,bottom=.08,wspace=.27,hspace=.38)
    for column,cp in enumerate((50,100,300)):
        for row,kind in enumerate(('reward','cost')):
            ax=axes[row,column];s=values[str(cp)]['critics'][kind]['phases']['all'];bins=s['equal_count_prediction_bins']
            x=np.asarray([b['prediction_mean'] for b in bins]);y=np.asarray([b['observed_return_mean'] for b in bins])
            lo=min(float(x.min()),float(y.min()));hi=max(float(x.max()),float(y.max()));margin=max((hi-lo)*.1,.01)
            ax.plot([lo-margin,hi+margin],[lo-margin,hi+margin],ls='--',color='#888888',label='예측=관측')
            ax.plot(x,y,'o-',color='#2865a8',label='예측값 5개 동일 개수 구간')
            ax.set_xlabel('구간별 가치 예측 평균');ax.set_ylabel('구간별 관측 MC return 평균')
            ax.set_title('체크포인트 %d · %s'%(cp,'보상' if kind=='reward' else '비용'));ax.grid(alpha=.15)
    axes[0,0].legend(fontsize=8)
    fig.suptitle('표본 return 기준 보정도(준비·음·말미 전체)\n한 궤적 안의 시점은 서로 상관되므로 기대 가치·인과관계의 인증이 아님')
    fig.savefig(BASE/'value_calibration_bins.png',dpi=160);plt.close(fig)
    lines=['# 고정 critic의 완결 에피소드 return 점검','',
        '**reward-value GAE residual 자체는 예측오차가 아니다.** 정당한 baseline 효과를 포함할 수 있는 가법 분해 항이다. 여기서는 별도로 저장된 Vr/Vc를 실제 관측한 완결 에피소드의 할인 return과 비교했다.','',
        '세 모델 모두 첫 에피소드128개가218틱에 자연 종료했음을 확인했다. 다음 에피소드의6틱은 제외했다. true terminal에서 return을 끝내고 critic bootstrap 없이 rewardγ=.99·costγ=1로 계산했다. 역방향 recurrence와 직접 할인합이 일치했다. H32 단위 기울기의 GAE·정규화는 재계산하거나 변경하지 않았다.','',
        '| cp | critic | 구간 | 표본 수 | MSE | 예측−관측 bias | 상관 |',
        '| --- | --- | --- | ---: | ---: | ---: | ---: |']
    phases_ko={'all':'전체','preparation':'준비','audible':'음','tail':'말미'}
    for cp in (50,100,300):
        for kind in ('reward','cost'):
            for phase,s in values[str(cp)]['critics'][kind]['phases'].items():
                correlation='정의 안 됨' if s['pearson_correlation'] is None else '%.4f'%s['pearson_correlation']
                lines.append('| %d | %s | %s | %d | %.5g | %.5g | %s |'%(cp,'보상' if kind=='reward' else '비용',phases_ko[phase],s['samples'],s['mse'],s['bias_prediction_minus_observed'],correlation))
    lines += ['',
        'cp300의 전체 reward MSE는 약0.000272로 cp50의0.13537·cp100의0.11890보다 작았다. 실패해 return 변동이 작은 해당 모델의 새 상태분포에서 얻은 결과이며, 같은 상태분포에 대한 critic 능력 순위는 아니다. 특히 cp300의 큰 reward-value residual gradient를 “critic 예측오차가 크다”는 뜻으로 읽을 수 없다. gradient의 residual 항은 baseline 관련 항이며 배치 공통 정규화의 영향도 받는다.','',
        '![시간별 가치와 관측 return](value_calibration_time_curves.png)','',
        '![예측값 구간별 관측 return](value_calibration_bins.png)','',
        '위 MSE·bias·상관과5개 동일 개수 예측 구간은 **한 번의 관측 return**을 기준으로 한 기술 통계다. 단일 return은 진짜 기대 가치가 아니며, 시점들은 같은 궤적에 속해 독립 표본이 아니다. 이 값만으로 critic이 퇴행을 일으켰다고 결론 내리지 않는다. 비용 관측 return은 모두0이므로 그 상관은 정의하지 않는다.','',
        'Vr/Vc는 각 행동 이전 관측의 값이다. 구간은 저장된60Hz 끝점 시각에서1/60초를 뺀 시각으로 나눴다. 준비180틱·음8틱·말미30틱이며 각 구간에서128환경을 모두 포함한다. 전체 표는 준비 구간이 길어 그 가중치가 크므로 구간별 표를 함께 본다.','',
        '[기계 판독 결과](value_calibration.json) · [첫 기울기 결과](RESULTS.md)']
    (BASE/'VALUE_CALIBRATION.md').write_text('\n'.join(lines)+'\n')
    outputs=[BASE/'value_calibration.json',BASE/'complete_episode_MC_returns.npz',BASE/'VALUE_CALIBRATION.md',BASE/'value_calibration_time_curves.png',BASE/'value_calibration_bins.png']
    verification=dict(completed=True,gpu_used=False,input_pins=before,inputs_unchanged=True,changed_inputs=changed,
        artifact_sha256={str(p):sha(p) for p in outputs},independent_review='pending root delegation')
    (BASE/'value_calibration_verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    print(json.dumps({cp:{kind:row['phases']['all'] for kind,row in v['critics'].items()} for cp,v in values.items()},indent=2))


if __name__=='__main__':main()
