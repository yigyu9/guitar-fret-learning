"""동일 원본에서 단독 변경 조건의 준비 후보를 생성한다. native 성공을 상속하지 않는다."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
import geometry

ROOT=geometry.ROOT
CONDITIONS=('baseline','joint_prepare','safe_route','robust_candidate','pad_feedback')
DEFAULT=ROOT/'docs/2026-11-02/압현실험/단일압현/전수검증_1-14_v1/로그/sweep_v1/geometry_frozen.json'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def generate(source,case,condition,out,max_nfev=40):
    source=Path(source).resolve();source.relative_to(ROOT)
    if condition not in CONDITIONS:raise ValueError('알 수 없는 단독 비교 조건')
    doc=json.loads(source.read_text())
    if not doc.get('completed'):raise ValueError('완료된 원본 기하 자료 필요')
    matches=[r for r in doc['rows'] if r['case_id']==case]
    if len(matches)!=1:raise ValueError('원본에서 단일 목표를 선택해야 함')
    for path,expected in doc['source_sha256'].items():
        resolved=Path(path);resolved=resolved if resolved.is_absolute() else ROOT/resolved
        resolved=resolved.resolve();resolved.relative_to(ROOT)
        if digest(resolved)!=expected:raise ValueError('기존 입력 SHA 불일치: '+path)
    row=copy.deepcopy(matches[0]);catalog=copy.deepcopy(doc['catalog_base']);planner=None
    catalog['diagnostic_condition']=condition
    evidence=dict(condition=condition,original_geometry=str(source),original_geometry_sha256=digest(source),
        original_case=case,changed_component=dict(baseline='none',joint_prepare='arm12 plus assigned finger4 endpoint',
        safe_route='sampled-clearance route only',robust_candidate='press candidate ranking only',
        pad_feedback='bounded measured pad feedback only')[condition],native_success_reused=False)
    if condition in ('joint_prepare','safe_route'):
        planner=geometry.Planner(catalog,row)
        goal=np.asarray(row['transport_waypoints'][-1]['q105'],dtype=float)
        if condition=='joint_prepare':
            goal,search=planner.endpoint(goal,max_nfev,joint_finger=True)
            evidence['endpoint_search']=search
            commands=[planner.q0,goal]
            row['geometry']=planner.measure(goal);row['candidate_valid']=row['geometry']['candidate_valid']
            row['transport_path_candidate_valid']=None
        else:
            _,path=planner.path(goal,max_nfev)
            evidence['path_search']=path
            commands=[np.asarray(q,dtype=float) for q in path['command_q105']]
            row['transport_path_candidate_valid']=path['candidate_valid']
        route=[]
        for i,q in enumerate(commands):
            metric=planner.measure(q)
            # 기존 최소2초 구간과0.5rad/s 평균 변위 기준을 그대로 사용한다.
            duration=0. if not i else max(2.,float(np.abs(q-commands[i-1]).max())/.5)
            route.append(dict(label='start' if not i else 'hover' if i==len(commands)-1 else 'clearance_waypoint',
                q105=q.tolist(),wrist_position_G_m=metric['wrist_position_G_m'],
                wrist_quaternion_G_xyzw=metric['wrist_quaternion_G_xyzw'],minimum_duration_s=duration,
                geometry=metric,native_verified=False))
        row['transport_waypoints']=route;row['q105']=goal.tolist()
        row['path_scope']='new explicit route; static clearance is not native physics proof'
    row['native_verified']=False
    row['diagnostic_condition']=condition
    row['diagnostic_changes']=evidence
    pins=dict(doc['source_sha256'])
    pins.update({str(source):digest(source),str(Path(__file__).resolve()):digest(__file__),
                 str(Path(geometry.__file__).resolve()):digest(geometry.__file__)})
    if planner:pins.update(planner.pins)
    result=dict(schema='guitar_learning.press_preparation_comparison.geometry.v1',completed=True,
        expected_total=1,rows=[row],catalog_base=catalog,source_sha256=pins,
        diagnostic_condition=condition,limitation='CPU 기하 후보이며 실제 압현 성공은 미검증',evidence=evidence)
    out=Path(out).resolve();out.relative_to(ROOT);out.mkdir(parents=True,exist_ok=False)
    geometry.write(out/'geometry.json',result)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=DEFAULT);parser.add_argument('--case',required=True)
    parser.add_argument('--condition',choices=CONDITIONS,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--max-nfev',type=int,default=40)
    args=parser.parse_args()
    if not 1<=args.max_nfev<=100:parser.error('max-nfev1~100')
    started=time.monotonic();result=generate(args.source,args.case,args.condition,args.out,args.max_nfev)
    print(json.dumps(dict(condition=args.condition,case=args.case,candidate=result['rows'][0]['candidate_valid'],
        elapsed_s=time.monotonic()-started),ensure_ascii=False))

if __name__=='__main__':main()
