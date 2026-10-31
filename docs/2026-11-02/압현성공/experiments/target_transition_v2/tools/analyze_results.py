"""두 음 전환의 첫32회 원장과 실제240Hz 목표 판정을 함께 검사한다."""
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def number(value):
    if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value):
        raise ValueError('유한한 수치가 필요함')
    return float(value)


def first_episodes(path):
    metadata=json.loads((path/'episode_metadata.json').read_text());first={}
    for line in (path/'episodes.jsonl').read_text().splitlines():
        row=copy.deepcopy(json.loads(line)['episode'])
        for field in metadata['fields']:
            current=row
            for key in field['path'][:-1]:current=current.setdefault(key,{})
            key=field['path'][-1]
            if key in current and current[key]!=field['value']:raise ValueError('공유 원장 충돌')
            current[key]=copy.deepcopy(field['value'])
        env=row['env_id']
        if type(env)is not int or not 0<=env<32:raise ValueError('최초32환경 필요')
        first.setdefault(env,row)
    if set(first)!=set(range(32)):raise ValueError('실패 포함 최초32환경 누락')
    return [first[i] for i in range(32)]


def analyze_evaluation(path):
    path=Path(path).resolve();report=json.loads((path/'report.json').read_text())
    if (not all(report.get(k)is True for k in ('completed','lifecycle_verified','first_episode_per_env_per_batch','failed_episodes_in_denominator'))
        or report.get('episodes')!=32 or any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))):
        raise ValueError('평가 완료/분모/입력 검증 실패')
    action_mode=json.loads((path/'action_mode.json').read_text())['action_mode']
    if action_mode not in ('mean','sampled'):raise ValueError('행동 방식 누락')
    config=report['settings']['transition'];schedule=config['schedule']
    if len(schedule)!=2 or [r['fret']for r in schedule]!=[6,7] or any(r['finger']!=2 or r['string_index']!=2 for r in schedule):
        raise ValueError('중지 같은3번줄6/7프렛 두 음 필요')
    rows=first_episodes(path);ids=[r['target_id'] for r in schedule]
    notes=[dict(target_id=r['target_id'],fret=r['fret'],onset_s=r['onset_s'],end_s=r['end_s'],success_count=0,
        mean_clean_s=0.,mean_wrong_s=0.,mean_missing_s=0.,full_duration_count=0,contact_observed_count=0,
        first_contact_s=[],first_achievement_s=[])for r in schedule]
    full=physical=wrist=full_duration=0;rewards={}
    for row in rows:
        ledger=row['left_note_ledger'];values=ledger['values'];obs=row['transition_diagnostics']
        if ledger['target_ids']!=ids or obs['target_ids']!=ids:raise ValueError('목표 원장 순서 변경')
        if any(len(values[k])!=2 for k in ('left','clean','wrong','missing')):raise ValueError('두 음 원장 필요')
        term=row['termination'];physical+=bool(term['physical_failure']);wrist+=bool(term['wrist_failure'])
        safe=bool(row['valid'])and not term['physical_failure']and not term['wrist_failure']
        achieved=[];held=[]
        for i,note in enumerate(notes):
            observed=number(row['task_time_s'])+1e-8>=schedule[i]['onset_s']
            ok=bool(values['left'][i])and observed;achieved.append(ok);note['success_count']+=ok
            for key in ('clean','wrong','missing'):note['mean_'+key+'_s']+=number(values[key][i])/32
            entire=values['clean'][i]+1e-8>=schedule[i]['end_s']-schedule[i]['onset_s']
            held.append(entire);note['full_duration_count']+=entire
            for key,source in (('first_contact_s','first_contact_s'),('first_achievement_s','first_achievement_s')):
                value=obs[source][i]
                if value is not None:
                    number(value)
                    if not schedule[i]['onset_s']-1e-8<=value<=schedule[i]['end_s']+1e-8:raise ValueError('시각 범위 오류')
                note[key].append(value)
            note['contact_observed_count']+=obs['first_contact_s'][i]is not None
        full+=safe and all(achieved);full_duration+=safe and all(held)
        for key,value in row['reward_components'].items():rewards[key]=rewards.get(key,0.)+number(value)/32
        if abs(sum(number(v)for v in row['reward_components'].values())-number(row['reward']))>1e-4:raise ValueError('보상 합계 불일치')
    trace=[[]for _ in range(32)];raw_dual=effective_dual=0
    with gzip.open(path/'finger_control_trace.jsonl.gz','rt')as stream:
        for line in stream:
            row=json.loads(line);extra=row['natural_preparation']['transition']
            for key in ('all_env_episode_time_s','all_env_episode_ids','all_env_candidate','all_env_wrong','all_env_raw_candidate','all_env_current_next_indices'):
                if len(extra[key])!=32:raise ValueError('전체32환경 추적 누락')
            for env in range(32):
                if extra['all_env_episode_ids'][env]!=rows[env]['finger_control_diagnostics']['episode_id']:continue
                candidate=extra['all_env_candidate'][env];wrong=extra['all_env_wrong'][env];raw=extra['all_env_raw_candidate'][env]
                if len(candidate)!=2 or len(wrong)!=2 or len(raw)!=2:raise ValueError('두 후보 필요')
                effective_dual+=all(candidate);raw_dual+=all(raw)
                trace[env].append((number(extra['all_env_episode_time_s'][env]),candidate,wrong,raw))
    if effective_dual:raise ValueError('같은 줄6/7프렛의 모순된 동시 유효 후보 재발')
    details=[];onset=schedule[1]['onset_s'];previous_end=schedule[0]['end_s']
    for env,points in enumerate(trace):
        if not points or points[0][0]>.02 or points[-1][0]+1/240+1e-8<rows[env]['task_time_s']:
            raise ValueError('최초 에피소드 전체 추적 누락')
        if any(abs((b[0]-a[0])-1/240)>2e-6 for a,b in zip(points,points[1:])):raise ValueError('240Hz 추적 누락/시간 역행')
        tail=[p for p in points if previous_end-.05-1e-8<=p[0]<previous_end-1e-8]
        start=next((p for p in points if p[0]>=onset-1e-8),None)
        timely=bool(start and start[0]-onset<=1/240+1e-8 and start[1][1]and not start[2][1])
        old_maintained=len(tail)>=11 and all(p[1][0]and not p[2][0]for p in tail)
        details.append(dict(env_id=env,previous_last50ms_clean=old_maintained,next_clean_at_onset=timely,
            on_time_with_previous_tail=old_maintained and timely,
            prior_raw_candidate_at_next_onset=(start[3][0]if start else None)))
    files=[path/name for name in ('report.json','episodes.jsonl','episode_metadata.json','action_mode.json','finger_control_trace.jsonl.gz')]
    return dict(schema='target_transition.analysis.v2',action_mode=action_mode,episodes=32,note_denominator=64,
        full_sequence_success_count=full,note_success_count=sum(n['success_count']for n in notes),full_duration_pair_count=full_duration,
        physical_failure_count=physical,wrist_failure_count=wrist,notes=notes,reward_term_means=rewards,
        on_time_with_previous_tail_count=sum(d['on_time_with_previous_tail']for d in details),transition_details=details,
        effective_dual_sample_count=effective_dual,raw_dual_sample_count=raw_dual,
        interpretation='0.6s 달성/음전체 유지/시작준수 별도. 낮은 이전 프렛의 raw접촉 잔류 자체는 높은 목표 실패조건이 아니다. 후보는 기하·몸체하중 proxy이며 실제음향이 아니다.',
        input_sha256={str(p):sha(p)for p in files})


def plot_study(root):
    """평균·확률 실행의 음별 달성과 유지 시간을 같은 축으로 기록한다."""
    rows=list(json.loads((root/'summary.json').read_text()).values())
    if not rows:return
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    rows.sort(key=lambda r:(r['seed'],r['updates'],r['action_mode']))
    labels=[f"seed{r['seed']} / {r['updates']} / {r['action_mode']}"for r in rows]
    counts=np.asarray([[n['success_count']for n in r['metrics']['notes']]for r in rows])
    clean=np.asarray([[n['mean_clean_s']for n in r['metrics']['notes']]for r in rows])
    fig,axes=plt.subplots(1,2,figsize=(10,max(4,.4*len(rows)+1.5)),constrained_layout=True)
    for ax,data,title,maximum in ((axes[0],counts,'음별 달성 / 32 (실패 포함)',32),(axes[1],clean,'평균 압현 유지 / 1.5초',1.5)):
        im=ax.imshow(data,vmin=0,vmax=maximum,cmap='YlGnBu',aspect='auto')
        ax.set_xticks([0,1]);ax.set_xticklabels(['A / fret6','B / fret7'])
        ax.set_yticks(range(len(rows)));ax.set_yticklabels(labels if ax is axes[0]else ['']*len(rows))
        ax.set_title(title,fontproperties=font)
        for i in range(len(rows)):
            for j in range(2):ax.text(j,i,str(int(data[i,j]))if maximum==32 else f'{data[i,j]:.2f}',ha='center',va='center',color='white'if data[i,j]>.65*maximum else 'black')
        fig.colorbar(im,ax=ax,shrink=.6)
    fig.suptitle('수정된 높은 프렛 판정 · 중지 A→B 전환',fontproperties=font)
    fig.savefig(root/'comparison.png',dpi=150);plt.close(fig)
    (root/'figure_provenance.json').write_text(json.dumps(dict(scope='first32 episodes per result; mean and sampled kept separate',
        input_sha256={str(root/'summary.json'):sha(root/'summary.json')}),ensure_ascii=False,indent=2)+'\n')
