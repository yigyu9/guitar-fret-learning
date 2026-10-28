"""CPU-only early-contact condition audit; reuse verified delayed-control results."""
import argparse
import ast
import csv
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PREVIOUS=BASE.parent/'contact_target_windup'
PRIOR=PREVIOUS/'analysis/results_v1'
spec=importlib.util.spec_from_file_location('verified_windup_analysis',PREVIOUS/'analysis/analyze.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
spec=importlib.util.spec_from_file_location('sealed_first_contact_driver',BASE/'run_probe.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)
read,sha,write,stats=previous.read,previous.sha,previous.write,previous.stats
LABELS=('original','no_new_inward','first_contact')
FILES=tuple('first_contact_report.json' if f=='target_windup_report.json' else f for f in previous.FILES)


def rows(path):
    with path.open() as stream:return list(csv.DictReader(stream))


def prior_csv(path):
    result=[]
    for row in rows(path):
        if row['condition'] not in LABELS[:2]:continue
        for k,v in row.items():
            if v=='':row[k]=None
            elif k not in ('condition','phase','population','metric','term'):
                if v in ('True','False'):row[k]=v=='True'
                else:row[k]=float(v)
        result.append(row)
    return result


def ready():
    required=[BASE/'run_01'/f for f in FILES]+[BASE/'01_launcher.json']
    return dict(ready=all(p.is_file() for p in required),missing=[str(p) for p in required if not p.is_file()])


def target_checks(t, threshold, mode):
    """Recompute every first-control gate, geometry dot and numerical constraint."""
    first = t['first_attempt']; gate = t['gate']
    expected = (first & ~t['prior_failure'] & ~t['stale_J'] & ~t['invalid_state']
        & ~t['invalid_J'] & (t['signed_normal_force_N'] > threshold))
    assert np.array_equal(gate, expected)
    g = np.einsum('tnc,tncj->tnj', t['normal_W'].astype(float), t['point_J'].astype(float))
    np.testing.assert_allclose(t['normal_J'], g, atol=1e-12, rtol=1e-12)
    assert np.array_equal(t['zero_J'], gate & (np.abs(g).max(-1) == 0))
    old, raw, final, actual = [t[k].astype(float) for k in ('old_target4', 'raw_target4', 'final_target4', 'actual4')]
    delta, request = final-old, raw-old
    for key, value in dict(old_normal_error_m=np.sum(g*(old-actual), -1), final_normal_error_m=np.sum(g*(final-actual), -1),
            raw_normal_increment_m=np.sum(g*request, -1), filtered_normal_increment_m=np.sum(g*delta, -1)).items():
        np.testing.assert_allclose(t[key], value, atol=1e-12, rtol=1e-12)
    displacement = np.einsum('tncj,tnj->tnc', t['point_J'].astype(float), final-raw)
    tangent = displacement-t['normal_W']*np.sum(displacement*t['normal_W'], -1, keepdims=True)
    np.testing.assert_allclose(t['tangent_change_m'], tangent, atol=1e-12, rtol=1e-12)
    L, U = t['lower_increment'], t['upper_increment']
    coordinate_tolerance = 8*np.finfo(np.float32).eps*np.maximum.reduce([np.abs(old), np.abs(raw), np.abs(final), np.ones_like(old)])
    excess = np.maximum.reduce([L-delta, delta-U, np.zeros_like(delta)])
    assert (excess[first] <= coordinate_tolerance[first]).all()
    assert (np.abs(delta)[first] <= 4/60+coordinate_tolerance[first]).all()
    np.testing.assert_allclose(t['box_excess_rad'][first], excess.max(-1)[first], atol=1e-15, rtol=1e-12)
    np.testing.assert_allclose(t['coordinate_tolerance_rad'][first], coordinate_tolerance.max(-1)[first], atol=1e-15, rtol=1e-12)
    changed = np.any(final != raw, -1)
    assert not changed[first & ~gate].any()
    if mode == 'original': assert not changed[first].any()
    else:
        capacity = np.sum(g*np.where(g > 0, U, np.where(g < 0, L, 0)), -1)
        beta = np.minimum(np.maximum(0, -np.sum(g*(old-actual), -1)), capacity) if mode.endswith('relax') else np.zeros_like(capacity)
        np.testing.assert_allclose(t['capacity_m'][gate], capacity[gate], atol=1e-12, rtol=1e-12)
        np.testing.assert_allclose(t['beta_m'][gate], beta[gate], atol=1e-12, rtol=1e-12)
        residual = np.sum(g*delta, -1)-beta
        np.testing.assert_allclose(t['halfspace_residual_m'][gate], residual[gate], atol=1e-12, rtol=1e-12)
        scale = np.max(np.abs(g), -1)
        normalized_beta = np.divide(beta, scale, out=np.zeros_like(beta), where=scale > 0)
        normalized_g = np.divide(g, scale[..., None], out=np.zeros_like(g), where=scale[..., None] > 0)
        tolerance = (np.sum(np.abs(normalized_g)*coordinate_tolerance, -1)+8*np.finfo(np.float32).eps*np.abs(normalized_beta))*scale
        np.testing.assert_allclose(t['halfspace_tolerance_m'][gate], tolerance[gate], atol=1e-15, rtol=1e-12)
        assert (residual[gate] >= -tolerance[gate]).all()
    assert not t['memory_submit_error_rad'][first].any() and not t['other_target_change_rad'][first].any()
    return changed, coordinate_tolerance


def first_events(t,a,metadata):
    """Snapshot immediately before target calculation; never a same-point contact claim."""
    result=[]
    changed=t['first_attempt'] & np.any(t['final_target4']!=t['raw_target4'],axis=-1)
    selected=[metadata['hand_joint_names'].index(n) for n in metadata['selected_joint_names']]
    plane=np.asarray(metadata['press_plane_G'],float)[:3]
    for kind,mask in (('first_gate',t['first_attempt'] & t['gate']),('first_change',changed)):
        for env in range(128):
            where=np.flatnonzero(mask[:,env]);r=dict(event=kind,env_id=env,start_clock=None,start_time_s=None,
                resultant_N=None,signed_press_N=None,qtarget_error_norm_deg=None,fixed_Jn_old_error_m=None,post_failure=None)
            for j in range(4):r['actual%d_deg'%j]=r['old_target%d_deg'%j]=r['target_error%d_deg'%j]=None
            if where.size:
                at=int(where[0]);clock=int(t['start_clock'][at,env]);assert clock>=4 and clock%4==0
                bodyforce=a['distal_force_W'][clock-1,env,2].astype(float)
                normal=previous.rotate(a['guitar_pose'][clock-1,env,3:7].astype(float),plane/np.linalg.norm(plane))
                actual=t['actual4'][at,env].astype(float);target=t['old_target4'][at,env].astype(float)
                np.testing.assert_array_equal(actual,a['actual_LH21'][clock-1,env,selected])
                np.testing.assert_array_equal(target,a['target_LH21'][clock-1,env,selected])
                signed=float(bodyforce@normal)
                np.testing.assert_allclose(signed,t['signed_normal_force_N'][at,env],rtol=2e-6,atol=1e-7)
                r.update(start_clock=clock,start_time_s=clock/240.,resultant_N=float(np.linalg.norm(bodyforce)),signed_press_N=signed,
                    qtarget_error_norm_deg=float(np.degrees(np.linalg.norm(target-actual))),
                    fixed_Jn_old_error_m=float(t['old_normal_error_m'][at,env]),post_failure=bool(t['post_failure'][at,env]))
                for j in range(4):
                    r['actual%d_deg'%j]=float(np.degrees(actual[j]));r['old_target%d_deg'%j]=float(np.degrees(target[j]));r['target_error%d_deg'%j]=float(np.degrees(target[j]-actual[j]))
            result.append(r)
    return result


def audit_new(source_a,source_c,source_eval,source_notes,original_t,t,a,c):
    """Reuse one existing condition auditor with only the explicit timing/report adapters."""
    prefix=driver.prefix_audit(t,a,c,source_a,source_c)
    report=read(BASE/'run_01/first_contact_report.json')
    assert prefix==report['prefix_audit']
    saved={k:getattr(previous,k) for k in ('BASE','FILES','read','target_checks','exact')}
    previous.BASE=BASE;previous.FILES=FILES;previous.target_checks=target_checks
    previous.read=lambda p:read(Path(p).with_name('first_contact_report.json') if Path(p).name=='target_windup_report.json' else p)
    # The legacy caller supplies its former fixed-prefix argument; never apply it.
    def actual_prefix(source,current,unused_fixed_prefix=None):
        return dict(prefix['physics_fields'],same_fields=prefix['checks']['physics_schema'])
    previous.exact=actual_prefix
    try:result=previous.analyze('01',source_a,source_c,source_eval,source_notes,original_t)
    finally:
        for k,v in saved.items():setattr(previous,k,v)
    summary,force,control,environment,reward,inputs=result
    summary['condition']='first_contact';summary['prefix_audit']=prefix
    summary['checks']['actual_preintervention_prefix']=all(prefix['checks'].values())
    summary.pop('original_source_exact');summary.pop('prefix_exact')
    for group in (force,control,environment,reward):
        for row in group:row['condition']='first_contact'
    return summary,force,control,environment,reward,inputs


def text(summaries,force,events,matched):
    lines=['# 최초 하중부터 증분 억제 — 실제 단일 timing 비교','',
        'matched 전제: **%s**. 원본/2초 지연 조건은 검수된 기존 결과를 재사용하고 첫 접촉 조건만 새로 감사했다.'%('충족' if matched else '미충족 — 효과 해석 보류'),'',
        '| 조건 | 달성/128 | clean / wrong 평균 | 물리 / 손목 실패 |','|---|---:|---:|---:|']
    for s in summaries:
        e=s['evaluation'];lines.append('|%s|%d|%.6f / %.6f|%d / %d|'%(s['condition'],round(e['achieved_fraction']*128),e['mean_clean_fraction'],e['mean_audible_wrong_fraction'],round(e['physical_failure_fraction']*128),round(e['wrist_failure_fraction']*128)))
    lines+=['','| 조건/구간 | 중지 resultant p50/p95/max N | 엄지 resultant p50/p95/max N |','|---|---:|---:|']
    for name in LABELS:
        for phase in ('audible','after'):
            cells=[]
            for body in ('selected','thumb'):
                r=next(r for r in force if r['condition']==name and r['phase']==phase and r['metric']==body+'_resultant_N')
                cells.append(' / '.join('미확보' if r[k] is None else '%.4f'%r[k] for k in ('p50','p95','max')))
            lines.append('|%s/%s|%s|%s|'%(name,phase,*cells))
    lines+=['','| 신규조건 event | 노출환경/128 | 시각 min/p50/max s | 직전 resultant p50 N | 직전 q-target 오차 norm p50 deg |','|---|---:|---:|---:|---:|']
    for kind in ('first_gate','first_change'):
        group=[r for r in events if r['event']==kind and r['start_clock'] is not None]
        def val(key):return stats([r[key] for r in group])
        time=val('start_time_s')
        cells=['미확보' if time[k] is None else '%.5f'%time[k] for k in ('min','p50','max')]
        lines.append('|%s|%d|%s|%s|%s|'%(kind,len(group),' / '.join(cells),val('resultant_N')['p50'],val('qtarget_error_norm_deg')['p50']))
    lines+=['','성과/유지/wrong/실패는 모든128 첫 시도 분모다. 힘은240Hz 실패 endpoint부터 제외하며60Hz 개입 통계는 실패로 끝난 control 전체를 제외한다. 환경별 첫실제변경 직전 physics/control prefix와 전체 명령 tape를검사했다. 고정480 gate/mask는 신규조건에 적용하지 않았다.', '',
        'first_events.csv는 없는 event도null로128환경씩 보존하고, 직전 실제 force·old target/actual4·Jn 오차를 담는다. control_by_phase.csv와 summary.json에는 실제 gate 노출, target/rate/box·부호·접선변경·J 속도잔차·original 대비 teacher 요청차가 있다. reward_payments.csv는 원9지급이며새조건 increment/cumulative/episode/음 원장과대조했다.', '',
        'body resultant는 접촉쌍 압력이 아니다. 고정material point는 최초any-candidate witness와다를수있다. 큰Jn·관절오차는침투mm가아니다. gate외저장0은0오차로평균하지않았다. 동일tape라도teacher feedback·자세·접선운동이달라질수있으므로 단독인과·자유손production개선·정책학습성과·새힘상한해결로확대하지않는다. 실제값검산과해석은후속독립검수를따른다.']
    return '\n'.join(lines)+'\n'


def self_test():
    source=(PREVIOUS/'analysis/analyze.py').read_text();old=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='target_checks')
    expected=ast.get_source_segment(source,old).replace("first & (t['start_clock'] >= 480) & ~t['prior_failure']","first & ~t['prior_failure']").replace("assert not changed[first & (t['start_clock'] < 480)].any() and not changed[first & ~gate].any()","assert not changed[first & ~gate].any()")
    new=next(n for n in ast.parse(Path(__file__).read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='target_checks')
    assert ast.dump(ast.parse(expected).body[0])==ast.dump(new)
    sys.path.insert(0,str(BASE))
    try:
        spec=importlib.util.spec_from_file_location('first_contact_cpu_fixture',BASE/'self_test.py')
        fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
        pool,trace=fixture.fixture.hook(driver.MODES[1])
        import torch
        for _ in range(5):pool.step(torch.full((128,39),.9))
        t=trace.values();assert t['gate'][1:].all() and (t['start_clock']<480).all()
        target_checks(t,.01,'first_contact')
        bad={k:v.copy() for k,v in t.items()};bad['gate'][1,0]=False
        try:target_checks(bad,.01,'first_contact')
        except AssertionError:pass
        else:raise AssertionError('tampered early gate accepted')
        assert not torch.cuda.is_initialized()
    finally:sys.path.remove(str(BASE))
    t=dict(first_attempt=np.zeros((2,128),bool),start_clock=np.tile(np.array([4,8])[:,None],(1,128)),
        gate=np.zeros((2,128),bool),raw_target4=np.zeros((2,128,4)),final_target4=np.zeros((2,128,4)),
        actual4=np.zeros((2,128,4)),old_target4=np.zeros((2,128,4)),signed_normal_force_N=np.zeros((2,128)),
        old_normal_error_m=np.zeros((2,128)),post_failure=np.zeros((2,128),bool))
    t['first_attempt'][:,0]=True;t['gate'][:,0]=True;t['final_target4'][1,0]=1
    t['old_target4'][0,0]=.1;t['old_target4'][1,0]=.2;t['signed_normal_force_N'][:,0]=1
    a=dict(actual_LH21=np.zeros((8,128,21)),target_LH21=np.zeros((8,128,21)),distal_force_W=np.zeros((8,128,5,3)),guitar_pose=np.zeros((8,128,13)))
    a['guitar_pose'][...,6]=1;a['distal_force_W'][[3,7],0,2,2]=1
    a['target_LH21'][3,0,:4]=.1;a['target_LH21'][7,0,:4]=.2
    metadata=dict(hand_joint_names=['j%d'%i for i in range(21)],selected_joint_names=['j%d'%i for i in range(4)],press_plane_G=[0,0,1,0])
    events=first_events(t,a,metadata)
    assert len(events)==256 and events[0]['start_clock']==4 and events[128]['start_clock']==8
    assert events[1]['start_clock'] is None and events[129]['resultant_N'] is None
    np.testing.assert_allclose(events[0]['qtarget_error_norm_deg'],np.degrees(.2))
    a['distal_force_W'][3,0,2,2]=2
    try:first_events(t,a,metadata)
    except AssertionError:pass
    else:raise AssertionError('mismatched event force was accepted')
    assert not ready()['ready'] or (BASE/'run_01/first_contact_report.json').exists()
    print(json.dumps(dict(completed=True,CPU_only=True,synthetic_only=True,checks=['timing-only analysis AST','early gate before480 accepted','tampered early gate rejected','first gate/change precontrol event and null exposure','event force mismatch rejected','native not executed'])))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true');parser.add_argument('--status',action='store_true');args=parser.parse_args()
    if args.self_test:self_test();return
    status=ready()
    if args.status or not status['ready']:print(json.dumps(status,indent=2));return
    out=HERE/'results_v1'
    if out.exists():raise FileExistsError(str(out))
    out.mkdir()
    try:
        prior_verify=read(PRIOR/'verification.json');assert prior_verify['completed'] and prior_verify['matched_interpretation_prerequisites']
        assert read(PRIOR/'review.json')['verdict']=='PASS'
        assert all(sha(p)==h for p,h in prior_verify['input_sha256'].items())
        oldsummary=read(PRIOR/'summary.json');summaries=[s for s in oldsummary['conditions'] if s['condition'] in LABELS[:2]]
        assert [s['condition'] for s in summaries]==list(LABELS[:2])
        source=previous.SOURCE
        sa,sc=previous.arrays(source/'physics240.npz'),previous.arrays(source/'control60.npz')
        se=read(source/'evaluation.json');sn=sorted(read(source/'first_attempt_notes.json'),key=lambda r:r['env_id'])
        original_t=previous.arrays(PREVIOUS/'run_original/target_control60.npz')
        t,a,c=[previous.arrays(BASE/'run_01'/f) for f in ('target_control60.npz','physics240.npz','control60.npz')]
        s,f,ctrl,env,reward,inputs=audit_new(sa,sc,se,sn,original_t,t,a,c);summaries.append(s)
        force=prior_csv(PRIOR/'force_by_phase.csv')+f;controls=prior_csv(PRIOR/'control_by_phase.csv')+ctrl
        environment=prior_csv(PRIOR/'environment_peaks.csv')+env;rewards=prior_csv(PRIOR/'reward_payments.csv')+reward
        events=first_events(t,a,read(BASE/'run_01/load_probe_report.json')['metadata'])
        matched=s['native_reports_pass'] and all(s['prefix_audit']['checks'].values())
        paths=[HERE/'analyze.py',HERE/'README.md',PREVIOUS/'analysis/analyze.py',BASE/'run_probe.py',BASE/'precommit.json',BASE/'fixed_inputs.npz']
        paths += [PRIOR/f for f in ('summary.json','verification.json','review.json','force_by_phase.csv','control_by_phase.csv','environment_peaks.csv','reward_payments.csv')]
        paths += [source/f for f in ('physics240.npz','control60.npz','evaluation.json','first_attempt_notes.json')]+[PREVIOUS/'run_original/target_control60.npz']
        inputs.update({str(p):sha(p) for p in paths})
        write(out/'summary.json',dict(matched_interpretation_prerequisites=matched,conditions=summaries,new_first_events=events))
        for name,data in (('force_by_phase.csv',force),('control_by_phase.csv',controls),('environment_peaks.csv',environment),('reward_payments.csv',rewards),('first_events.csv',events)):previous.output_csv(out/name,data)
        oldcases=previous.CASES
        try:previous.CASES=LABELS;previous.plot(out/'summary.png',force,controls)
        finally:previous.CASES=oldcases
        with (out/'RESULTS.md').open('x') as stream:stream.write(text(summaries,force,events,matched))
        assert all(sha(p)==h for p,h in inputs.items())
        write(out/'verification.json',dict(completed=True,CPU_only=True,matched_interpretation_prerequisites=matched,input_files_unchanged=True,input_sha256=inputs,new_condition_checks=s['checks']))
        print(json.dumps(dict(completed=True,output=str(out),matched_interpretation_prerequisites=matched)))
    except BaseException as error:
        if not (out/'verification.json').exists():write(out/'verification.json',dict(completed=False,CPU_only=True,failure=dict(type=type(error).__name__,message=str(error))))
        raise


if __name__=='__main__':main()
