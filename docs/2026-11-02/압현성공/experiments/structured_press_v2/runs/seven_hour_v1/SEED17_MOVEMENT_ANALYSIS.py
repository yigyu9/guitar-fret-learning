"""seed17 고정 저장본의 전체 episode 관절 분담과 실제 음 구간을 CPU로 검토한다."""
from pathlib import Path
import json
import gzip
from datetime import datetime,timezone
import numpy as np
import DISCOUNTED_REWARD_ANALYSIS as audit

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'full33_seed17/evaluate'
JOINTS=('LH:index1_x','LH:index1_z','LH:index2','LH:index3')
LABELS=tuple(str(n)+'_'+mode for n in (100,200) for mode in ('latent_mean','requested_angle_mean'))


def note_trace(path,pins):
    source=path/'native/finger_control_trace.jsonl.gz'
    if not source.exists():return dict(status='not_recorded')
    pins[str(source)]=audit.sha(source)
    with gzip.open(source,'rt') as stream:raw=[json.loads(line) for line in stream]
    result=dict(status='completed',scope='only recorded environments, not assumed all32; first episode;3<t<=5.5',environments={})
    for env in sorted(set(x['env_id'] for x in raw)):
        episode=min(x['episode_id'] for x in raw if x['env_id']==env)
        rows=[x for x in raw if x['env_id']==env and x['episode_id']==episode and 3+1e-12<x['episode_time_s']<=5.5+1e-12]
        if not rows:
            result['environments'][str(env)]=dict(status='no_note_samples',episode_id=episode);continue
        steps=[x['episode_physics_step'] for x in rows]
        if len(steps)!=len(set(steps)):raise ValueError('note trace duplicate physics step')
        names=rows[0]['joint_names'];stats={}
        for joint in JOINTS:
            j=names.index(joint);values={k:np.rad2deg(np.array([x[k][j] for x in rows])) for k in
                ('requested_target_rad','applied_target_rad','actual_rad')}
            stats[joint]={k:dict(mean_deg=float(v.mean()),std_deg=float(v.std()),range_deg=float(np.ptp(v))) for k,v in values.items()}
            stats[joint]['request_minus_applied_rms_deg']=float(np.sqrt(np.mean((values['requested_target_rad']-values['applied_target_rad'])**2)))
            stats[joint]['applied_minus_actual_rms_deg']=float(np.sqrt(np.mean((values['applied_target_rad']-values['actual_rad'])**2)))
        result['environments'][str(env)]=dict(status='full_note_window' if steps==list(range(721,1321)) else 'partial_note_window',
            episode_id=episode,samples=len(rows),control_ticks=len(set(x['control_tick'] for x in rows)),
            first_time_s=rows[0]['episode_time_s'],last_time_s=rows[-1]['episode_time_s'],joints=stats)
    return result


def pair(first,second):
    if first['status']!='completed' or second['status']!='completed':return dict(verified=False,reason='자료 미완료')
    if first['checkpoint_sha256']!=second['checkpoint_sha256']:return dict(verified=False,reason='저장본 SHA 다름')
    if any(not np.array_equal(first['initial'][k],second['initial'][k]) for k in ('q105','hold105')):
        return dict(verified=False,reason='실제 q/hold 행별 대응 실패')
    return dict(verified=True,scope='same checkpoint and32 q/hold rows; complete body/root initial states not audited')


def collect():
    pins={str(Path(__file__)):audit.sha(Path(__file__)),str(Path(audit.__file__)):audit.sha(Path(audit.__file__))}
    rows={};errors=[]
    for label in LABELS:
        path=BASE/label
        try:
            row=audit.load_dataset(path,pins)
            if row['status']=='completed':
                summary=audit.read(path/'summary.json');expected=label.split('_',1)[1]
                if summary.get('deployment_rule')!=expected or summary.get('saved_gaussian_mean_std_unchanged') is not True:
                    raise ValueError('실행 규칙 provenance 불일치')
                settings=path/'native/settings.json';pins[str(settings)]=audit.sha(settings)
                if audit.read(settings)['seed']!=17:raise ValueError('seed17 저장 설정 아님')
                episodes=[x['episode'] for x in audit.analyze_all.iter_episode_rows(path/'native')]
                names=episodes[0]['left_finger_motion']['joint_names'];joints={}
                for joint in JOINTS:
                    ix=names.index(joint);joints[joint]={}
                    for k in ('actual_range_rad','actual_min_rad','actual_max_rad','target_range_rad'):
                        joints[joint][k.replace('_rad','_deg')]=float(np.rad2deg(np.mean([e['left_finger_motion']['values'][k][ix] for e in episodes])))
                limits={k:max(max(e['left_finger_motion']['values'][k]) for e in episodes) for k in
                    ('actual_native_limit_fraction','target_native_limit_fraction','limit_outward_command_fraction')}
                row.update(whole_episode_joints=joints,all21_native_limit_max=limits,note_trace=note_trace(path,pins),
                    native_note_means_s={k:float(np.mean([e['left_note_ledger']['values'][k][0] for e in episodes])) for k in
                        ('clean','best_clean_streak','wrong','missing','geometry_time','loaded_target_time','own_wrong_string_time','other_higher_time')})
            rows[label]=row
        except (OSError,ValueError,KeyError) as error:rows[label]=dict(status='invalid',error=str(error));errors.append(label+': '+str(error))
    pairing={str(n):pair(rows[str(n)+'_latent_mean'],rows[str(n)+'_requested_angle_mean']) for n in (100,200)}
    all_initial_same=None
    if all(row['status']=='completed' for row in rows.values()):
        baseline=rows[LABELS[0]]['initial'];all_initial_same=all(np.array_equal(baseline[k],x['initial'][k]) for x in rows.values() for k in ('q105','hold105'))
    ready=all(x['verified'] for x in pairing.values()) and all_initial_same is True
    for row in rows.values():row.pop('initial',None);row.pop('curve_mean',None)
    audit.verify_pins(pins)
    return dict(schema='seed17_movement_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),datasets=rows,
        actual_pairing=pairing,all_four_actual_q_hold_same=all_initial_same,comparison_ready=ready,errors=errors,input_sha256=pins,
        scope='independently trained seed17, one fixed index goal and nominal v9 initial DOF pose repeated32; not new-song/pose generalization',
        interpretation='완료·source·실제초기 대응 전 효과 판단 보류' if not ready else
            '대응 비교 가능; 압현 성공 복구와 자연스러운 관절 협응은 별개이며 큰 진폭 자체가 자연스러움의 기준도 아님')


def write(result):
    lines=['# seed17 실제 손가락 움직임 분석','','집계: '+result['updated_utc'],'',result['scope'],'',
        '| 조건 | 상태 | 안전성공/분모 | 총clean초 | 최장연속clean초 | MCP범위° | 벌림범위° | PIP범위° | DIP범위° |',
        '|---|---|---|---|---|---|---|---|---|']
    for name,row in result['datasets'].items():
        m=row.get('metrics',{});js=row.get('whole_episode_joints',{})
        lines.append('| {} | {} | {}/{} | {} | {} | {} | {} | {} | {} |'.format(name,row['status'],
            *[m.get(k) for k in ('safe_success','count','mean_clean_s','mean_best_clean_s')],
            *[round(js[j]['actual_range_deg'],3) if j in js else None for j in JOINTS]))
    lines+=['','비교 준비: '+str(result['comparison_ready']),'',result['interpretation'],'',
        '실제 대응: `'+json.dumps(result['actual_pairing'],ensure_ascii=False)+'`','',
        '범위는 첫32개 episode별 max−min의 평균이며 reset 각도를 seed로 포함하고 이후60Hz 완료tick에서 갱신된다. '
        '한계 점유율도60Hz 표본으로 전체240Hz 극값을 인증하지 않는다. 작은 손가락 변화로 성공해도 자연스러운 압현을 학습했다는 증거는 아니다. '
        '몸체 pose 없이 손 전체 운반의 기여율은 계산하지 않는다.','',
        '음 구간의 요청/적용/실제각 시간 평균·std는 기록된 환경만 사용한다. trace가 env0뿐이면32환경 평균이 아니며 '
        '조기종료나 기록부족은 partial로 표시한다. 구체적인21축 한계·목표각 범위·원시 압현기하/하중/오압현과SHA는 JSON에 기록했다.']
    for name,row in result['datasets'].items():
        if row['status']=='completed':
            lines+=['','### '+name+' 음 구간 기록','','`'+json.dumps(row['note_trace'],ensure_ascii=False)+'`']
    (ROOT/'SEED17_MOVEMENT_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'SEED17_MOVEMENT_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(dict(comparison_ready=result['comparison_ready'],errors=result['errors'])))
