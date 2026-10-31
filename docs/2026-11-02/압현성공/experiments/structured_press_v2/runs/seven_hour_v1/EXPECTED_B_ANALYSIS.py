"""B 지원을 그대로 둔 요청각 기댓값 진단을 실제32환경 대응 후 집계한다."""
from datetime import datetime,timezone
import json
from pathlib import Path
import numpy as np
import DISCOUNTED_REWARD_ANALYSIS as audit
import fixed_reset_evaluate as fixed

ROOT=Path(__file__).resolve().parent
CONTROLS=dict(index_B0=ROOT/'paired_B_initial_seed4242',index_B100=ROOT/'paired_B_100_seed4242',
    pinky_B0=ROOT/'pinky_B_seed7_v1/100/evaluate_initial_fixed4242',
    pinky_B100=ROOT/'pinky_B_seed7_v1/100/evaluate_final_fixed4242')
CASES=dict(pinky_B100_latent_mean=('pinky_B100','latent_mean'),
    index_B0_requested_angle_mean=('index_B0','requested_angle_mean'),
    index_B100_requested_angle_mean=('index_B100','requested_angle_mean'),
    pinky_B0_requested_angle_mean=('pinky_B0','requested_angle_mean'),
    pinky_B100_requested_angle_mean=('pinky_B100','requested_angle_mean'))


def load(path,pins,mode=None):
    report_path=path/'report.json'
    if not report_path.exists():return dict(status='pending',path=str(path))
    report=audit.read(report_path)
    if report.get('completed') is not True:return dict(status='pending_or_failed',path=str(path),failure=report.get('expected_B_failure',report.get('failure')))
    if (report.get('lifecycle_verified') is not True or report.get('original_strict_load_completed') is not True or
        report.get('source_weights_unchanged') is not True or report.get('optimizer_updates_in_evaluation')!=0 or
        report.get('first_episode_per_env') is not True or report.get('failed_episodes_in_denominator') is not True or
        report.get('reset_seed')!=4242 or any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))):
        raise ValueError('B native/strict/0update/first32/reset 검증 누락')
    config=report['settings']['structured_press'];finger=config['finger']
    expected=list(range(12))+list(range(17+4*('index','middle','ring','pinky').index(finger),21+4*('index','middle','ring','pinky').index(finger)))
    if config['stage']!='B' or config['active_axes']!=expected or len(expected)!=16:raise ValueError('actual saved B16 계약 불일치')
    snapshot=audit.read(path/'inputs_before.json');audit.verify_pins(snapshot);pins.update(snapshot)
    if mode is not None:
        if (report.get('deployment_rule')!=mode or report.get('policy_mode')!='saved_B16_'+mode or
            report.get('saved_gaussian_mean_std_unchanged') is not True or report.get('optimizer_updates_difference')!=0 or
            any(report.get(k) is not True for k in ('stage_B_support_unchanged','initial_distribution_unchanged','clamp_unchanged')) or
            report.get('per_step_discounted_return_available') is not False or
            report.get('deterministic_policy_unchanged')!=(mode=='latent_mean')):raise ValueError('B 배포mode/지원 보존 provenance 누락')
        execution=report.get('execution_audit',{});calls=execution.get('act_calls',0)
        if not execution.get('strict_loaded') or calls<=0 or execution.get('inactive_exact_calls')!=calls or execution.get('active_point_exact_calls')!=calls:
            raise ValueError('실제16·23축/strict act 증거 누락')
        audit.verify_pins(report['expected_B_input_sha256']);pins.update(report['expected_B_input_sha256'])
    checkpoint=Path(report['checkpoint']);checkpoint_sha=audit.sha(checkpoint)
    if checkpoint_sha!=report['checkpoint_sha256'] or checkpoint_sha!=report['source_sha256']:raise ValueError('source checkpoint SHA 불일치')
    import torch
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if payload['identity']['architecture']['schema']!='guitar_learning.structured_press_policy.v2':raise ValueError('BASE policy required')
    codec=payload['identity']['architecture']['contract']['action']['target_contract']
    catalog_paths=[Path(name) for name,sha in snapshot.items() if Path(name).name=='catalog.json' and sha==config['geometry_sha256']]
    if len(catalog_paths)!=1:raise ValueError('actual catalog pin 식별 불가')
    catalog=audit.read(catalog_paths[0]);indices=[codec['joint_names'].index(name) for name in codec['action_order']]
    reference=np.asarray(codec['reference105_rad'])[indices];lo=np.asarray(codec['action_lower_rad']);hi=np.asarray(codec['action_upper_rad'])
    if (indices!=catalog['action_indices'] or len(indices)!=39 or not np.allclose(reference,np.asarray(catalog['reference105'])[indices],atol=1e-6,rtol=0) or
        not np.allclose(lo,catalog['action_lower'],atol=1e-6,rtol=0) or not np.allclose(hi,catalog['action_upper'],atol=1e-6,rtol=0)):
        raise ValueError('actual39 codec/catalog 불일치')
    episodes=[row['episode'] for row in audit.analyze_all.iter_episode_rows(path)]
    if len(episodes)!=32 or {e['env_id'] for e in episodes}!=set(range(32)):raise ValueError('raw unique first32 불일치')
    metrics=audit.analyze_all.combine_episode_values(episodes,finger)
    metrics['raw_note_means_s']={key:float(np.mean([e['left_note_ledger']['values'][key][0] for e in episodes])) for key in ('clean','best_clean_streak','wrong','missing')}
    if metrics['max_reward_reconciliation_error']>2e-5 or metrics['max_cost_reconciliation_error']>2e-5:raise ValueError('raw9term/cost 합 불일치')
    initial=report['initial_conditions']
    if initial['count']!=32 or len(initial['environments'])!=32 or {e['env_id'] for e in initial['environments']}!=set(range(32)):
        raise ValueError('actual q/hold32 분모 불일치')
    for row in initial['environments']:
        if any(np.asarray(row[key]).shape!=(105,) or not np.isfinite(row[key]).all() for key in ('q105','initial_hold105')):
            raise ValueError('actual q/hold 유한성/shape 불일치')
    for p in (report_path,path/'inputs_before.json',path/'episodes.jsonl',path/'episode_metadata.json',checkpoint):pins[str(p)]=audit.sha(p)
    return dict(status='completed',path=str(path),metrics=metrics,reset_seed=4242,initial_conditions=initial,
        checkpoint_sha256=checkpoint_sha,source_updates=payload['updates'],finger=finger,song=config['song'],
        codec=dict(action_order=codec['action_order'],reference39=reference.tolist(),positive_span39=(hi-reference).tolist(),negative_span39=(reference-lo).tolist(),catalog_sha256=config['geometry_sha256']),
        reward_gamma=report['settings']['ppo']['gamma'],cost_gamma=report['settings']['ppo']['cost_gamma'],
        metric_scope='undiscounted raw first32 episode means; no per-step discounted-return claim')


def paired(a,b):
    if a.get('status')!='completed' or b.get('status')!='completed':return dict(verified=False,reason='자료 대기')
    if a['checkpoint_sha256']!=b['checkpoint_sha256'] or a['codec']!=b['codec']:return dict(verified=False,reason='동일source/codec 아님')
    try:return fixed.assert_same_initial_conditions(a,b)
    except ValueError as error:return dict(verified=False,reason=str(error))


def baseline_equal(a,b):
    fields=('count','safe_success','failure_episodes','mean_reward','mean_cost','mean_clean_s','mean_safe_clean_s','mean_best_clean_s',
        'reward_components_mean','cost_components_mean','raw_note_means_s','complete_episode_control_transitions')
    bad=[k for k in fields if a.get(k)!=b.get(k)]
    return dict(verified=not bad,mismatched_fields=bad,scope='원시32episode 성과/9항/cost/clean/wrong/missing exact; 전체각/실행action journal 동등성 아님')


def gate(result):
    reasons=[]
    for name in CONTROLS:
        if result['controls'].get(name,{}).get('status')!='completed':reasons.append(name+' control 미완료')
    for name in CASES:
        if result['experiments'].get(name,{}).get('status')!='completed':reasons.append(name+' 미완료/invalid')
        if result['actual_pairing'].get(name,{}).get('verified') is not True:reasons.append(name+' source/qhold 대응 미검증')
    if result['pinky_baseline_reproduction'].get('verified') is not True:reasons.append('소지B100 latent 기준 재현 미검증')
    return dict(ready=not reasons,reasons=reasons)


def collect():
    pins={str(Path(__file__)):audit.sha(Path(__file__)),str(Path(audit.__file__)):audit.sha(Path(audit.__file__)),str(Path(fixed.__file__)):audit.sha(Path(fixed.__file__))}
    result=dict(schema='expected_B_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),controls={},experiments={},actual_pairing={},errors=[],input_sha256=pins,
        pinky_baseline_reproduction=dict(verified=False,reason='자료 대기'),production_unchanged=True,per_step_discounted_return_available=False)
    for group,paths in (('controls',CONTROLS),('experiments',{name:ROOT/'expected_B'/name for name in CASES})):
        for name,path in paths.items():
            try:result[group][name]=load(path,pins,CASES[name][1] if group=='experiments' else None)
            except (ValueError,KeyError,OSError) as error:
                result[group][name]=dict(status='invalid',path=str(path),error=str(error));result['errors'].append(group+'/'+name+': '+str(error))
    for name,(control,mode) in CASES.items():result['actual_pairing'][name]=paired(result['controls'][control],result['experiments'][name])
    a,b=result['controls']['pinky_B100'],result['experiments']['pinky_B100_latent_mean']
    if result['actual_pairing']['pinky_B100_latent_mean']['verified']:
        result['pinky_baseline_reproduction']=baseline_equal(a['metrics'],b['metrics'])
    result['gate']=gate(result);result['interpretation']='완료/실제 B지원 보존/source/qhold/기준 재현 증거 전 효과 판단 보류'
    if result['gate']['ready']:
        result['interpretation']={name:dict(requested_minus_latent_success=result['experiments'][name]['metrics']['safe_success']-result['controls'][control]['metrics']['safe_success'],
            requested_minus_latent_safe_clean_s=result['experiments'][name]['metrics']['mean_safe_clean_s']-result['controls'][control]['metrics']['mean_safe_clean_s'],
            requested_minus_latent_cost=result['experiments'][name]['metrics']['mean_cost']-result['controls'][control]['metrics']['mean_cost'])
            for name,(control,mode) in CASES.items() if mode=='requested_angle_mean'}
    for group in ('controls','experiments'):
        for row in result[group].values():row.pop('initial_conditions',None)
    audit.verify_pins(pins)
    return result


def write(result):
    lines=['# B16 요청각 기댓값 배포 진단','','집계: '+result['updated_utc'],'',
        '저장 BASE B16의 aligned 초기 후보·reset4242·팔 press 지원/clamp·물리·분포·가중치를 유지하고 실행 요청만 비교한다. '
        'B clamp 제거 실험이나 free33 평가와 합산하지 않는다. 새 학습/목표 일반화 검사가 아니다.','',
        '| 자료 | 상태 | 안전성공/분모 | safe clean초 | wrong초 | missing초 | raw reward | raw cost |','|---|---|---:|---:|---:|---:|---:|---:|']
    for group in ('controls','experiments'):
        for name,row in result[group].items():
            m=row.get('metrics',{});note=m.get('raw_note_means_s',{})
            lines.append('| {} | {} | {}/{} | {} | {} | {} | {} | {} |'.format(name,row['status'],m.get('safe_success'),m.get('count'),m.get('mean_safe_clean_s'),note.get('wrong'),note.get('missing'),m.get('mean_reward'),m.get('mean_cost')))
    for title,key in (('실제source/39codec/qhold 대응','actual_pairing'),('소지B100 latent 재현','pinky_baseline_reproduction'),('완료 gate','gate'),('진단 결과','interpretation')):
        lines+=['','## '+title,'','`'+json.dumps(result[key],ensure_ascii=False)+'`']
    lines+=['','보상9항과 비용은 실패 포함 원시 최초32 episode의 비할인 평균이다. 저장된 PPO gamma를 JSON에 기록하지만 per-step trace가 없어 할인 보상을 계산했다고 주장하지 않는다. '
        'latent baseline 재현은 기록된 성과/보상/비용/clean·wrong·missing 범위의 exact 비교이며 전체각 journal 동등성은 아니다. '
        'q105/hold105의 실제32행 대응은 body/root 전체 물리 상태 동등성을 보장하지 않는다.','',
        '요청각 기댓값은 **유지한 B 지원 clamp·평활화·속도제한 이전**의 요청에 적용된다. 최종 supported target이나 실제 물리 응답의 기댓값이 아니다. '
        '결과가 달라도 비대칭 decoder를 모든 실패의 단독 원인으로 확정하지 않는다. inactive23/active16의 실제act 검증과 유한 latent/logp·source 모델0update provenance가 있어야 판단한다. '
        '기존 최고 모델과 생산 코드는 자동 교체하지 않는다. source SHA·9항·cost·실제실패·원시분모·gammas는 JSON에 있다.']
    (ROOT/'EXPECTED_B_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'EXPECTED_B_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(dict(gate=result['gate'],errors=result['errors']),ensure_ascii=False))
