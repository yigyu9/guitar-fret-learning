"""진행 중인 학습을 건드리지 않고 최초100개 완결 업데이트만 집계한다."""
from pathlib import Path
from collections import Counter, defaultdict
import datetime
import gzip
import hashlib
import json
import math
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[3]
STUDY = PROJECT / 'docs/2026-11-09/압현_v5_C1_장기학습_v1'
RUNTIME = STUDY / '작업자료/runtime'
RUN = RUNTIME / 'study_outputs/학습/attempt01/J'
sys.path.insert(0, str(RUNTIME))
from guitar_learning.training.training_log_io import _restore_episode

CUTOFF = 100


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def prefix_rows(path, key, maximum):
    """미완성 행과 이후 갱신을 제외하고, 실제 읽은 완결 prefix의 SHA를 남긴다."""
    digest, used = hashlib.sha256(), 0
    with path.open('rb') as stream:
        for raw in stream:
            if not raw.endswith(b'\n'):
                raise ValueError('분석 경계 전에 미완성 JSONL: '+str(path))
            row = json.loads(raw)
            if int(row[key]) > maximum:
                break
            digest.update(raw)
            used += len(raw)
            yield row
    evidence[str(path)] = dict(prefix_bytes=used, prefix_sha256=digest.hexdigest(),
        note='계속 커지는 파일 전체 SHA가 아니라 분석에 사용한 prefix')


def avg(values):
    return float(np.mean(values)) if values else None


def window(rows):
    episodes = sum(r['episode_summary']['count'] for r in rows)
    transitions = sum(r['transitions'] for r in rows)
    collect = sum(r['collection_s'] for r in rows)
    update = sum(r['update_s'] for r in rows)
    result = dict(first=rows[0]['optimizer_updates'], last=rows[-1]['optimizer_updates'],
        updates=len(rows), transitions=transitions, collection_s=collect, update_s=update,
        collection_fraction=collect/(collect+update), transitions_per_s=transitions/(collect+update),
        median_collection_s=float(np.median([r['collection_s'] for r in rows])),
        median_update_s=float(np.median([r['update_s'] for r in rows])),
        episodes=episodes, actor_lr_min=min(r['actor_lr'] for r in rows),
        actor_lr_last=rows[-1]['actor_lr'], kl_retries=sum(r['kl_retries'] for r in rows),
        achieved_per_ended_episode=sum(r['episode_summary']['mean_left_success_count']*
            r['episode_summary']['count'] for r in rows)/episodes if episodes else None,
        terminal_counts={key: sum(r['episode_summary'][key] for r in rows)
            for key in ('timeline_complete', 'physical_failure', 'wrist_failure')},
        mean_reward_per_transition=sum(r['mean_reward']*r['transitions'] for r in rows)/transitions,
        mean_cost_per_transition=sum(r['mean_cost']*r['transitions'] for r in rows)/transitions)
    for name in ('reward', 'cost'):
        critics = [r['diagnostics']['post_update']['critics'][name] for r in rows]
        result[name+'_critic_EV_median'] = float(np.median([c['explained_variance'] for c in critics]))
        result[name+'_value_std_median'] = float(np.median([c['value']['std'] for c in critics]))
        result[name+'_target_std_median'] = float(np.median([c['target']['std'] for c in critics]))
    result['advantage_cost_reward_std_ratio_median'] = float(np.median([
        r['diagnostics']['advantages']['cost_raw']['std']/r['diagnostics']['advantages']['reward_raw']['std']
        for r in rows]))
    result['reward_component_means'] = {key: sum(r['reward_component_means'][key]*r['transitions']
        for r in rows)/transitions for key in rows[0]['reward_component_means']}
    result['std_geometric_mean33_last'] = math.exp(rows[-1]['diagnostics']['post_update'][
        'latent_gaussian_entropy']['mean']/33 - .5*math.log(2*math.pi*math.e))
    return result


evidence = {}
metrics = list(prefix_rows(RUN/'learning_metrics.jsonl', 'optimizer_updates', CUTOFF))
assert [r['optimizer_updates'] for r in metrics] == list(range(1, CUTOFF+1))
# 작은 metrics 원문만 별도 보존한다. 큰 episode·trace는 원본 참조와 prefix SHA를 쓴다.
(HERE/'metrics_u0001_0100.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in metrics))
metadata = json.loads((RUN/'episode_metadata.json').read_text())
contract = json.loads((RUN/'training_contract.json').read_text())
schedule = contract['task']['provenance']['song']['schedule']
by_id = {r['target_id']:r for r in schedule}
per_note = defaultdict(Counter)
counts, diagnostic = Counter(), defaultdict(lambda: np.zeros(21))
v4_sums = defaultdict(lambda: np.zeros(4))
diagnostic_samples = 0
for row in prefix_rows(RUN/'episodes.jsonl', 'update_index', CUTOFF-1):
    episode = _restore_episode(row['episode'], metadata)
    counts['ended_episodes'] += 1
    counts['scope_'+episode['finger_skill']['scope']] += 1
    counts['physical_samples'] += episode['finger_control_diagnostics']['completed_physics_samples']
    counts['any_legacy_success_episodes'] += episode['song']['left_success_count'] > 0
    ledger = episode['left_note_ledger']
    for i, target_id in enumerate(ledger['target_ids']):
        if not ledger['focus_mask'][i]:
            continue
        target, values = by_id[target_id], ledger['values']
        note = per_note[target['mapping_note_index']]
        note['selected'] += 1
        note['exposed'] += values['exposure_time'][i] > 0
        note['loaded_candidate'] += values['loaded_target_time'][i] > 0
        note['achieved_raw_ledger'] += bool(values['left'][i])
        note['clean_s'] += values['clean'][i]
        note['required_audible_s'] += target['end_s']-target['onset_s']
        note['wrong_s'] += values['wrong'][i]
        note['missing_s'] += values['missing'][i]
    samples = episode['finger_control_diagnostics']['completed_physics_samples']
    diagnostic_samples += samples
    for key, values in episode['finger_control_diagnostics']['values'].items():
        if key.endswith('_rms'):
            diagnostic[key] += np.square(np.asarray(values))*samples
    for key in ('target_exposed_s','preparing_s','actual_gate_s','aligned_s','distance_integral_m_s'):
        v4_sums[key] += np.asarray(episode['compact_press_v4']['values'][key])

assert counts['ended_episodes'] == sum(r['episode_summary']['count'] for r in metrics)
native = {key: np.sqrt(values/diagnostic_samples).tolist() for key, values in diagnostic.items()}
trace = []
with gzip.open(RUN/'finger_control_trace.jsonl.gz', 'rt') as stream:
    for line in stream:
        row = json.loads(line)
        if row['substep'] == 4:
            trace.append(row)
request = np.asarray([r['requested_target_rad'][5:] for r in trace])
applied = np.asarray([r['applied_target_rad'][5:] for r in trace])
actual = np.asarray([r['actual_rad'][5:] for r in trace])
trace_summary = dict(scope='env0 최초600 control ticks, 검지~소지16축, substep4만; 이후수렴과구분',
    control_ticks=len(trace), axis_samples=int(request.size),
    requested_applied_gap_above_1e4_fraction=float(np.mean(np.abs(request-applied)>1e-4)),
    requested_applied_gap_rms_rad=float(np.sqrt(np.mean((request-applied)**2))),
    applied_actual_gap_rms_rad=float(np.sqrt(np.mean((applied-actual)**2))),
    requested_actual_gap_rms_rad=float(np.sqrt(np.mean((request-actual)**2))))
hardware = json.loads((HERE/'자원표본.json').read_text())
summary = dict(captured_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    cutoff_updates=CUTOFF, source_run=str(RUN), evidence=evidence,
    all=window(metrics), first20=window(metrics[:20]), last20=window(metrics[-20:]),
    episode_denominator_note='완결된 학습 episode만; 진행중1024환경 또는 고정전곡평가의 성공률이 아님',
    ended_episode_counts=dict(counts), notes=[dict(source_index=i,**v) for i,v in sorted(per_note.items())],
    v4_sums={key:value.tolist() for key,value in v4_sums.items()},
    native_diagnostic_sample_weighted_rms=native, early_trace=trace_summary,
    resource_sample=dict(samples=len(hardware), start=hardware[0]['time_utc'], end=hardware[-1]['time_utc'],
        gpu_util_mean=avg([r['gpu_util_percent'] for r in hardware]),
        gpu_util_min=min(r['gpu_util_percent'] for r in hardware),
        gpu_util_max=max(r['gpu_util_percent'] for r in hardware),
        gpu_used_MiB_max=max(r['gpu_used_MiB'] for r in hardware),
        gpu_power_mean_W=avg([r['gpu_power_W'] for r in hardware]),
        cpu_mean_sum=avg([sum(p['cpu_percent'] for p in r['processes']) for r in hardware]),
        cpu_scope='관련 프로세스 합; 100%는논리CPU한개'))
for name in ('settings.json','training_contract.json','episode_metadata.json','finger_control_trace.jsonl.gz'):
    p=RUN/name
    evidence[str(p)] = dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
write(HERE/'초반100회_분석.json', summary)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fonts = [Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf'),
         Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]
from matplotlib import font_manager
for font in fonts:
    if font.exists():
        font_manager.fontManager.addfont(str(font)); plt.rcParams['font.family']=font_manager.FontProperties(fname=str(font)).get_name();break
plt.rcParams['axes.unicode_minus']=False
out=HERE.parent/'그림';out.mkdir(exist_ok=True)
x=np.arange(1,len(metrics)+1)
fig, axes=plt.subplots(2,2,figsize=(13,9))
axes[0,0].stackplot(x,[r['collection_s'] for r in metrics],[r['update_s'] for r in metrics],
                   labels=['경험 수집','PPO 갱신'],colors=['#3c83b8','#e4a64a'])
axes[0,0].set_ylabel('반복당 초');axes[0,0].legend();axes[0,0].set_title('계산 시간의 대부분은 수집')
for name,label in [('reward','보상 가치망'),('cost','비용 가치망')]:
    axes[0,1].plot(x,[r['diagnostics']['post_update']['critics'][name]['explained_variance'] for r in metrics],label=label)
axes[0,1].set_title('초반 가치 예측의 설명력');axes[0,1].set_ylabel('설명 분산 EV');axes[0,1].legend()
for key,label in [('reward_raw','보상 advantage'),('cost_raw','비용 advantage')]:
    axes[1,0].plot(x,[r['diagnostics']['advantages'][key]['std'] for r in metrics],label=label)
axes[1,0].set_title('행동 학습 신호의 크기');axes[1,0].set_ylabel('표준편차');axes[1,0].legend()
note_rows=summary['notes'];n=[r['source_index']+1 for r in note_rows]
axes[1,1].bar(n,[r['selected'] for r in note_rows],label='선택 기회',color='#8bc0df')
axes[1,1].bar(n,[r['loaded_candidate'] for r in note_rows],label='한 번이라도 하중 후보',color='#d77f4c')
axes[1,1].set_xticks(n);axes[1,1].set_title('종료 episode의 목표별 기회와 접촉');axes[1,1].legend(fontsize=9)
axes[1,1].set_xlabel('원본 목표 번호');axes[1,1].set_ylabel('episode 수')
for ax in (axes[0,0],axes[0,1],axes[1,0]):ax.set_xlabel('업데이트')
fig.suptitle('C1 v5 초기100회 진단 — 최종 성능 평가 아님',fontsize=16)
fig.tight_layout();fig.savefig(out/'초반학습진단.png',dpi=160);plt.close(fig)

fig,ax=plt.subplots(figsize=(10,5))
t=np.arange(0,241)/60
ax.plot(t,.99**(t*60),label='보상 할인 γ=0.99')
ax.plot(t,(.99*.98)**(t*60),label='GAE 계수 (γλ), λ=0.98')
ax.axvline(32/60,color='#d77f4c',linestyle='--',label='현재 수집창 H32 = 0.533초')
ax.axvline(128/60,color='#4e917c',linestyle=':',label='비교 후보 H128 = 2.133초')
ax.set_xlabel('이전 행동과 결과 사이 시간(초)');ax.set_ylabel('분석적으로 계산한 계수')
ax.set_title('수집창 밖의 결과는 가치망 예측을 통해 전달됨');ax.legend();ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(out/'시간할인과수집창.png',dpi=160);plt.close(fig)
print(json.dumps({k:summary[k] for k in ('cutoff_updates','all','last20','early_trace','resource_sample')},ensure_ascii=False,indent=2))
