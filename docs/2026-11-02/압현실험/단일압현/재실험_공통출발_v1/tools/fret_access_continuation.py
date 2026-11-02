"""이미 재현한 중지12F 두 자세에서 이웃 프렛으로 이어가는 CPU 국소 탐색.

S1/S3 중지 고정 대기각의 source 기하 후보만 검사한다. 검지·6번 줄이나 실제
native 연주 가능 범위로 일반화하지 않으며, 미발견은 불가능 판정이 아니다.
"""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
PLANNER=HERE/'prepare_transport_v2.py'
PLANNER_SHA='6e39ef07567a1575c065eaccdcd6ad4ec80b6ed77fed406a823fc4be5ef3556c'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(path)


def run(out,max_nfev=20,budget_s=240.):
    if out.exists():raise FileExistsError('기존 출력 덮어쓰기 금지')
    if sha(PLANNER)!=PLANNER_SHA:raise ValueError('현재 CPU planner SHA 불일치')
    spec=importlib.util.spec_from_file_location('fret_continuation_current_planner',PLANNER)
    planner_module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=planner_module;spec.loader.exec_module(planner_module)
    out.mkdir(parents=True)
    pins={str(PLANNER):PLANNER_SHA,str(Path(__file__).resolve()):sha(__file__)}
    catalogs={};last_valid={};baselines=[];fallbacks=[]
    for string in (1,3):
        case='middle_s'+str(string)+'_f12';path=HERE.parent/'inputs_v2'/case/'catalog.json'
        document,prov=planner_module.verify_inputs(path,path.with_name('provenance.json'))
        row=document['goals'][0];goal=dict(finger='middle',finger_id=2,string=string-1,physical_string=string,fret=12)
        planner=planner_module.Planner(document,goal);q=np.array(row['final_hover_q105']);metric=planner.measure(q)
        pins.update(planner.pins)
        for p in (path,path.with_name('provenance.json')):pins[str(p.resolve())]=sha(p)
        baselines.append(dict(case=case,seed_catalog=str(path.resolve()),geometry=metric,candidate_valid=metric['candidate_valid'],q105=q.tolist(),native=False))
        catalogs[string]=document;last_valid[string]=dict(fret=12,q=q)
    write(out/'baseline_reproduction.json',dict(schema='fret_continuation_baseline.v1',rows=baselines,source_sha256=pins))
    if not all(r['candidate_valid']for r in baselines):raise ValueError('정확한 known-valid 12F 기준2/2 재현 필요')
    for path in (BASE/'입력/전체기타후보').glob('middle_*/catalog.json'):
        document,prov=planner_module.verify_inputs(path,path.with_name('provenance.json'))
        fallback=document['goals'][0];fallbacks.append((fallback,path))
        for p in (path,path.with_name('provenance.json')):pins[str(p.resolve())]=sha(p)
    goals=[dict(finger='middle',finger_id=2,string=string-1,physical_string=string,fret=fret)
           for fret in range(13,23) for string in (1,3)]
    write(out/'endpoint_goals.json',dict(schema='fret_continuation_goals.v1',goals=goals,
        scope='explicit source_geometry goals; no learning/song bundle'))
    pins[str((out/'endpoint_goals.json').resolve())]=sha(out/'endpoint_goals.json')
    start=time.monotonic();rows=[]
    report=dict(schema='guitar_learning.fret_access_middle_continuation.v1',completed=False,
        scope='middle finger, standard strings1/3 only; fixed v9 all fingers/thumb, same arm12 action bounds',
        baseline_reproduced=2,max_nfev_per_seed=max_nfev,wall_budget_s=budget_s,
        candidate_criterion=dict(height_m=[.005,.015],tangent_max_m=.005,facing_min=.1,source_shape_gap_min_m=.002),
        seed_schedule='previous successful neighbor; only on failure also original closest v5 candidate',
        limitation='Source endpoint geometry only, not native stability or trajectory; finite search misses do not certify physical impossibility',rows=rows,source_sha256=pins)
    for goal in goals:
        if time.monotonic()-start>=budget_s:
            rows.append(dict(**goal,status='not_tested_time_budget',candidate_valid=None));continue
        string=goal['physical_string'];planner=planner_module.Planner(catalogs[string],goal);pins.update(planner.pins)
        seed=last_valid[string];before=time.monotonic()
        q,search=planner.endpoint(seed['q'],max_nfev)
        attempts=[dict(seed_kind='previous_valid_neighbor',seed_fret=seed['fret'],search=search)]
        if not search['geometry']['candidate_valid'] and time.monotonic()-start<budget_s:
            fallback,path=min(fallbacks,key=lambda pair:abs(pair[0]['fret']-goal['fret'])+2*abs(pair[0]['string']-goal['string']))
            second,second_search=planner.endpoint(fallback['q105'],max_nfev)
            attempts.append(dict(seed_kind='closest_original_v5',seed_case=fallback['case'],seed_catalog=str(path.resolve()),search=second_search))
            if second_search['geometry']['candidate_valid']:q,search=second,second_search
        valid=bool(search['geometry']['candidate_valid'])
        fixed=np.setdiff1d(np.arange(105),planner.arm)
        if not np.array_equal(q[fixed],planner.q0[fixed]):raise ValueError('고정된 비팔 관절 변경')
        row=dict(**goal,status='cpu_geometry_candidate' if valid else 'not_found_fixed_standby_local_search',
            candidate_valid=valid,previous_valid_fret=seed['fret'],elapsed_s=time.monotonic()-before,
            attempts=attempts,geometry=search['geometry'],q105=q.tolist(),native_verified=False)
        rows.append(row)
        if valid:last_valid[string]=dict(fret=goal['fret'],q=q.copy())
        report['elapsed_s']=time.monotonic()-start;write(out/'results.json',report)
        print('middle',string,goal['fret'],valid,round(row['elapsed_s'],2),flush=True)
    report.update(completed=True,elapsed_s=time.monotonic()-start,
        counts=dict(total=len(rows),tested=sum(r['candidate_valid']is not None for r in rows),candidate=sum(r['candidate_valid']is True for r in rows),
                    not_found=sum(r['candidate_valid']is False for r in rows),not_tested=sum(r['candidate_valid']is None for r in rows)),
        last_valid_fret_by_string={str(s):v['fret']for s,v in last_valid.items()})
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('Input changed during continuation '+path)
    write(out/'results.json',report)
    print(json.dumps(report['counts']),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--max-nfev',type=int,default=20)
    parser.add_argument('--budget-s',type=float,default=240.)
    args=parser.parse_args();run(args.out.resolve(),args.max_nfev,args.budget_s)
