"""동일 B16에서 press 팔 clamp만 제거한 고정 평가를 CPU에서 검증한다."""
from pathlib import Path
import json
from datetime import datetime,timezone
import compare_variance as comparison
import fixed_reset_evaluate as fixed
import DISCOUNTED_REWARD_ANALYSIS as audit

ROOT=Path(__file__).resolve().parent
CONTROLS=dict(pinky_B0=ROOT/'pinky_B_seed7_v1/100/evaluate_initial_fixed4242',
    pinky_B100=ROOT/'pinky_B_seed7_v1/100/evaluate_final_fixed4242',
    index_B0=ROOT/'paired_B_initial_seed4242',index_B100=ROOT/'paired_B_100_seed4242')


def load(path,finger,pins,unclamped):
    row=comparison.collect_run(path,True,pins)
    if row['status']!='completed':return row
    report=comparison.read(path/'report.json')
    if not report.get('original_strict_load_completed') or not report.get('lifecycle_verified') or any(
            report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors','execution_diagnostic_failure')):
        raise ValueError('strict native lifecycle 무결성 실패')
    if report.get('reset_seed')!=4242:raise ValueError('reset4242 계약 불일치')
    if unclamped:
        if report.get('execution_override')!='remove_B_press_arm_clamp_only' or report.get('official_B_promotion') is not False:
            raise ValueError('clamp-only provenance 누락')
        if report.get('source_model_exact_unchanged') is not True or report.get('optimizer_updates_difference')!=0:
            raise ValueError('모델/optimizer 불변 증거 누락')
        audit.verify_pins(report['execution_input_sha256']);pins.update(report['execution_input_sha256'])
        if not isinstance(report.get('source_sha256'),str) or report['source_sha256']!=report['checkpoint_sha256']:
            raise ValueError('checkpoint SHA 계약 불일치')
    row['metrics']=comparison.analysis.aggregate(path,finger,True)
    return row


def pair_gate(control,probe):
    if control['status']!='completed' or probe['status']!='completed':return dict(verified=False,reason='자료 미완료')
    if control['source_checkpoint_sha256']!=probe['source_checkpoint_sha256']:
        return dict(verified=False,reason='동일 저장 source checkpoint SHA 아님')
    return fixed.assert_same_initial_conditions(control,probe)


def collect():
    pins={str(Path(__file__)):audit.sha(Path(__file__)),str(Path(comparison.__file__)):audit.sha(Path(comparison.__file__)),
        str(Path(fixed.__file__)):audit.sha(Path(fixed.__file__))};cases={};errors=[]
    for name,control in CONTROLS.items():
        row={};finger=name.split('_')[0]
        for mode,path in (('control',control),('unclamped',ROOT/'unclamped_B'/name)):
            try:row[mode]=load(path,finger,pins,mode=='unclamped')
            except (OSError,KeyError,ValueError) as error:row[mode]=dict(status='invalid',error=str(error));errors.append(name+'/'+mode+': '+str(error))
        try:row['actual_pairing']=pair_gate(row['control'],row['unclamped'])
        except ValueError as error:row['actual_pairing']=dict(verified=False,reason=str(error));errors.append(name+': '+str(error))
        cases[name]=row
    audit.verify_pins(pins)
    ready=all(row['actual_pairing']['verified'] for row in cases.values())
    return dict(schema='unclamped_B_analysis.v1',updated_utc=datetime.now(timezone.utc).isoformat(),cases=cases,
        comparison_ready=ready,errors=errors,input_sha256=pins,
        scope='같은 저장 B정책·16축·aligned/reset4242에서 press 팔 clamp만 제거; free33/v9 전환 아님',
        interpretation='원시32/모델/source/실제초기대응 검증 전 효과 판단 보류' if not ready else
            '네 대응 진단 비교 가능; 공식 B 승급·일반화 주장이 아님')


def write(result):
    lines=['# B 압현 단계 팔 제한 단일 요인 진단','','집계: '+result['updated_utc'],'',result['scope'],'',
        '| 조건 | 실행 | 상태 | 안전 성공/분모 | clean초 | wrong예산 보상 | cost |','|---|---|---|---|---|---|---|']
    for name,row in result['cases'].items():
        for mode in ('control','unclamped'):
            item=row[mode];m=item.get('metrics',{})
            lines.append('| {} | {} | {} | {}/{} | {} | {} | {} |'.format(name,mode,item['status'],m.get('safe_success'),m.get('count'),
                m.get('mean_safe_clean_s'),m.get('reward_components_mean',{}).get('song_wrong_press'),m.get('mean_cost')))
    lines+=['','전체 비교 준비: '+str(result['comparison_ready']),'',result['interpretation'],'',
        '실제 초기 대응: `'+json.dumps({k:v['actual_pairing'] for k,v in result['cases'].items()},ensure_ascii=False)+'`','',
        '원본 strict source·평균 정책·관측 단계·초기 분포·활성축·물리·보상·native rate/smoothing은 유지한다. '
        '실패도 첫32 episode 분모에 포함하고, 9항과 비용·실제 초기 q/hold는 JSON 원시 증거로 확인한다. '
        'free33/v9 성공과 B 실패의 차이를 이 진단 이전에 clamp 원인으로 확정하지 않는다.']
    (ROOT/'UNCLAMPED_B_ANALYSIS.md').write_text('\n'.join(lines)+'\n')
    (ROOT/'UNCLAMPED_B_ANALYSIS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    result=collect();write(result);print(json.dumps(dict(comparison_ready=result['comparison_ready'],errors=result['errors'])))
