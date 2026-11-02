"""충돌 없는 native 유지 검사의 팔 처짐을 오프라인 목표각 feedforward로 보정한다.

초기 관절·몸체·손가락·물리·보상은 유지하며 원본을 덮어쓰지 않는다.
보정은 팔12축 gain0.7, 최초 유지 목표 대비 축별0.12rad 이내다.
새 후보는 native_verified=false이며 별도 native 재검사를 받아야 한다.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
GAIN, LIMIT = .7, .12


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def row_identity(row):
    value={key:item for key,item in row.items() if key not in ('native_verified','native_validation')}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def calibrate(catalog, report, diagnostic):
    """검사 근거가 완결된 단일 후보에서 팔 목표각만 바꾸어 반환한다."""
    import math
    if (report.get('completed') is not True or report.get('failure') or report.get('changed_inputs')
            or report.get('hold_ticks')!=180 or report.get('control_hz')!=60 or report.get('physics_hz')!=240):
        raise ValueError('완결된 불변 입력180tick native 검사 필요')
    samples=report.get('samples',[])
    if len(samples)!=180 or [sample['tick'] for sample in samples]!=list(range(1,181)):
        raise ValueError('180개 native 제어 끝점 필요')
    for sample in samples:
        if (sample.get('finite') is not True or any(sample['terminated']) or any(sample['truncated'])
                or any(any(row) for key in ('candidate','wrong') for row in sample[key])):
            raise ValueError('비유한·종료·선접촉·오압현 상태는 feedforward 보정 금지')
    rows=[row for row in catalog['goals'] if report['case'] in (row.get('case'),row.get('case_id'))]
    if len(rows)!=1 or report.get('candidate_sha256')!=row_identity(rows[0]):
        raise ValueError('probe와 입력 후보 identity 불일치')
    if diagnostic.get('case')!=report['case']:
        raise ValueError('서로 다른 조합의 진단 사용 금지')
    endpoints=diagnostic.get('endpoints',[])
    if len(endpoints)!=2 or [e['control_tick'] for e in endpoints]!=[1,180]:
        raise ValueError('첫/마지막 native 관절·몸체 진단 필요')
    for endpoint in endpoints:
        if endpoint['joint_names']!=catalog['joint_names'] or len(endpoint['q105'])!=105:
            raise ValueError('native 관절순서·길이 불일치')
        # 몸체 합력은 충돌쌍 인증이 아니다. 근거의 양 끝에서 힘이 있으면 보정하지 않는다.
        for name,force in zip(endpoint['logical_body_names'],endpoint['contact_force']):
            if name.startswith('human/LH:') or name=='human/L_Wrist':
                if any(not math.isfinite(v) for v in force) or sum(v*v for v in force)>.01**2:
                    raise ValueError('손·손목에 하중이 있는 후보 보정 금지: '+name)
    row=rows[0];actual=endpoints[-1]['q105']
    if endpoints[-1]['physics_step']!=720 or endpoints[-1]['initial_q105']!=row['q105']:
        raise ValueError('native 끝점 또는 초기 관절 identity 불일치')
    original=row.get('holding_feedforward',{}).get('original_hold105',row['hold_target105'])
    if any(len(value)!=105 for value in (original,row['hold_target105'],row['q105'])):
        raise ValueError('105축 유지·초기각 필요')
    result=copy.deepcopy(catalog)
    updated=next(r for r in result['goals'] if r['song']==row['song'])
    details=[]
    for slot,(name,index) in enumerate(zip(catalog['active_names'][:12],catalog['action_indices'][:12])):
        if not name.startswith('L_') or catalog['joint_names'][index]!=name:
            raise ValueError('팔12축 순서 계약 불일치')
        error=row['q105'][index]-actual[index]
        requested=row['hold_target105'][index]+GAIN*error
        lower=max(catalog['action_lower'][slot],original[index]-LIMIT)
        upper=min(catalog['action_upper'][slot],original[index]+LIMIT)
        if lower>upper or not all(math.isfinite(v) for v in (error,requested,lower,upper)):
            raise ValueError('비유한 보정 또는 유효 범위 교집합 없음')
        applied=min(upper,max(lower,requested))
        updated['hold_target105'][index]=applied
        details.append(dict(name=name,joint_index=index,actual_rad=actual[index],initial_rad=row['q105'][index],
            previous_hold_rad=row['hold_target105'][index],error_rad=error,requested_rad=requested,
            applied_rad=applied,delta_rad=applied-row['hold_target105'][index],
            cumulative_delta_rad=applied-original[index],clipped=applied!=requested,
            allowed_range_rad=[lower,upper]))
    updated.pop('native_validation',None)
    updated['native_verified']=False
    result['native_verified']=False
    updated['holding_feedforward']=dict(schema='guitar_learning.single18.holding_feedforward.v1',
        gain=GAIN,max_cumulative_axis_delta_rad=LIMIT,original_hold105=original,
        scope='offline arm12 command compensation only; initial q/body, fingers/thumb, PD/reward/termination unchanged',
        force_evidence='first and last endpoint native resultant <=0.01N; not full-time pair contact certification',
        corrections=details)
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--provenance',type=Path,required=True)
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--case')
    args=parser.parse_args(argv)
    catalog_path,provenance_path,probe,out=[p.resolve() for p in (args.catalog,args.provenance,args.probe,args.out)]
    for path in (catalog_path,provenance_path,probe,out):path.relative_to(ROOT)
    if out.exists():raise FileExistsError('기존 출력 덮어쓰기 금지: '+str(out))
    provenance=json.loads(provenance_path.read_text())
    if digest(catalog_path)!=provenance['catalog_sha256']:raise ValueError('catalog SHA 불일치')
    pins=dict(provenance['active_physical_inputs'])
    for name,expected in pins.items():
        path=Path(name) if Path(name).is_absolute() else ROOT/name
        if digest(path)!=expected:raise ValueError('기존 입력 변경: '+name)
    report_path=probe/'report.json';diagnostic_path=probe/'native_endpoint_diagnostics.json'
    report=json.loads(report_path.read_text());diagnostic=json.loads(diagnostic_path.read_text())
    if args.case is not None and args.case!=report['case']:
        raise ValueError('요청 조합과 원본 probe 조합 불일치')
    runtime=Path(__file__).with_name('runtime.py')
    if digest(runtime)!=report['runtime_sha256']:raise ValueError('실제 검사 실행기 SHA 불일치')
    before=json.loads((probe/'inputs_before.json').read_text())
    for name,expected in before.items():
        if digest(name)!=expected:raise ValueError('probe 봉인 입력 변경: '+name)
    result=calibrate(json.loads(catalog_path.read_text()),report,diagnostic)
    for path in (catalog_path,provenance_path,report_path,diagnostic_path,probe/'inputs_before.json',runtime,Path(__file__).resolve()):
        pins[str(path)]=digest(path)
    out.mkdir(parents=True)
    write(out/'catalog.json',result)
    provenance.update(catalog_sha256=digest(out/'catalog.json'),active_physical_inputs=pins,
        holding_feedforward=dict(source_catalog=str(catalog_path),source_probe=str(probe),gain=GAIN,limit_rad=LIMIT))
    provenance.pop('native_validation',None)
    write(out/'provenance.json',provenance)
    row=next(r for r in result['goals'] if report['case'] in (r.get('case'),r.get('case_id')))
    settings=json.loads((probe/'settings.json').read_text())
    corrections=row['holding_feedforward']['corrections']
    write(out/'report.json',dict(schema='guitar_learning.single18.hold_calibration_report.v1',
        completed=True,case=report['case'],seed=settings['seed'],native_verified=False,
        source_catalog=str(catalog_path),source_probe=str(probe),
        changed_axes=[c['name'] for c in corrections if c['delta_rad']!=0.],
        corrections=corrections,clipped_axes=[c['name'] for c in corrections if c['clipped']],
        requires_new_native_probe=True,catalog_sha256=digest(out/'catalog.json')))


if __name__=='__main__':main()
