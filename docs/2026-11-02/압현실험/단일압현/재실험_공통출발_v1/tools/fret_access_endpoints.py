"""현재 팔 행동 범위·고정 대기각에서 36개 endpoint 기하 후보를 짧게 탐색한다.

현재 독립 CPU planner만 정확한 SHA로 재사용한다. 가상 목표는 학습 bundle이
아닌 명시적 string/fret/finger 데이터다. 국소 탐색 미발견은 불가능 판정이 아니다.
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
PLANNER_PATH=HERE/'prepare_transport_v2.py'
PLANNER_SHA='6e39ef07567a1575c065eaccdcd6ad4ec80b6ed77fed406a823fc4be5ef3556c'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def run(out,max_nfev=20,budget_s=240):
    if out.exists():raise FileExistsError('기존 출력 덮어쓰기 금지')
    if sha(PLANNER_PATH)!=PLANNER_SHA:raise ValueError('현재 CPU planner SHA 불일치')
    spec=importlib.util.spec_from_file_location('fret_endpoint_current_planner',PLANNER_PATH)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    goals=[dict(case=finger+'_s'+str(string)+'_f'+str(fret),finger=finger,finger_id=i,
                string=string-1,physical_string=string,fret=fret)
           for fret in (12,15,16,17,19,22) for finger,i in (('index',1),('middle',2)) for string in (1,3,6)]
    pins={str(PLANNER_PATH):PLANNER_SHA,str(Path(__file__).resolve()):sha(__file__)}
    seeds={}
    for p in (BASE/'입력/후보').glob('*/catalog.json'):
        if p.parent.name.split('_')[0] not in ('index','middle'):continue
        provenance=p.with_name('provenance.json')
        catalog,metadata=module.verify_inputs(p,provenance)
        pins[str(p.resolve())]=sha(p);pins[str(provenance.resolve())]=sha(provenance)
        for row in catalog['goals']:
            seeds[row['case']]=(catalog,row,p)
    if not seeds:raise ValueError('불변 기존 후보 데이터 필요')
    out.mkdir(parents=True);write(out/'endpoint_goals.json',dict(schema='fret_endpoint_goals.v1',goals=goals,
        scope='explicit source_geometry goals only; no song or learning bundle generated'))
    pins[str((out/'endpoint_goals.json').resolve())]=sha(out/'endpoint_goals.json')
    rows=[];start=time.monotonic()
    for goal in goals:
        if time.monotonic()-start>=budget_s:
            rows.append(dict(**goal,status='not_tested_time_budget',candidate_valid=None));continue
        matching=[v for v in seeds.values() if v[1]['finger']==goal['finger']]
        catalog,seed,path=min(matching,key=lambda item:abs(item[1]['fret']-goal['fret'])+2*abs(item[1]['string']-goal['string']))
        # 기존 row의 song/bundle을 복제하지 않는다. 새 목표는 기하 데이터만이다.
        geometry_goal={k:v for k,v in goal.items()if k!='case'}
        planner=module.Planner(catalog,geometry_goal)
        goal_start=time.monotonic();q,search=planner.endpoint(seed['q105'],max_nfev)
        pins.update(planner.pins)
        fixed=np.setdiff1d(np.arange(105),planner.arm)
        if not np.array_equal(q[fixed],planner.q0[fixed]):raise ValueError('고정 대기각/비팔 축 변경 발견')
        metric=search['geometry']
        row=dict(**goal,status='cpu_geometry_candidate' if metric['candidate_valid'] else 'not_found_local_fixed_standby',
            candidate_valid=bool(metric['candidate_valid']),elapsed_s=time.monotonic()-goal_start,
            seed_catalog=str(path.resolve()),seed_case=seed['case'],search=search,q105=q.tolist(),native_verified=False)
        rows.append(row)
        report=dict(schema='guitar_learning.fret_access_fixed_standby_endpoints.v1',completed=len(rows)==len(goals),
            max_nfev=max_nfev,wall_budget_s=budget_s,elapsed_s=time.monotonic()-start,
            condition=dict(fingers='index/middle; all LH finger/thumb angles fixed to common v9',
                arm='same production action bounds, arm12 only',native=False,trajectory=False,
                source_collision='full hand18 vs full guitar89 source convex; no anatomical certificate',
                endpoint=dict(height_m=[.005,.015],tangent_max_m=.005,facing_min=.1,source_shape_gap_min_m=.002)),
            rows=rows,source_sha256=pins,
            limitation='Finite single-seed local search <=max_nfev; not found does not mean physically impossible; source candidate is not native success')
        write(out/'results.json',report)
        print(goal['case'],row['status'],round(row['elapsed_s'],2),flush=True)
    report['completed']=True;report['elapsed_s']=time.monotonic()-start
    report['counts']=dict(total=len(rows),tested=sum(r['candidate_valid'] is not None for r in rows),
        candidate=sum(r['candidate_valid'] is True for r in rows),not_found=sum(r['candidate_valid'] is False for r in rows),
        not_tested=sum(r['candidate_valid'] is None for r in rows))
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('Input changed during CPU endpoint scan: '+path)
    write(out/'results.json',report)
    lines=['# 현재 제어·고정 대기각의 짧은 endpoint 탐색','',
        '각 조합은 동일한 팔 행동 범위에서 최대 '+str(max_nfev)+'회 국소 탐색했다. 후보 발견은 소스 기하 조건만 만족했다는 뜻이며, 미발견도 실제 불가능의 증거가 아니다.','',
        '| 손가락 | 프렛 | 1번 줄 | 3번 줄 | 6번 줄 |','|---|---:|---|---|---|']
    for finger in ('index','middle'):
        for fret in (12,15,16,17,19,22):
            cells=[]
            for string in (1,3,6):
                r=next(r for r in rows if r['finger']==finger and r['fret']==fret and r['physical_string']==string)
                cells.append('후보 발견' if r['candidate_valid'] is True else '미발견' if r['candidate_valid'] is False else '미검사')
            lines.append('| '+finger+' | '+str(fret)+' | '+' | '.join(cells)+' |')
    lines+=['','원시 목표·선택 seed·최종 관절각·거리·입력 SHA는 endpoint_goals.json/results.json에 기록했다.',
        '학습과 native/GPU 실행은 하지 않았다. 프렛17~22 연구 보류는 안전을 위한 운영 범위이며 물리적 불가능 판정이 아니다.']
    (out/'현재제어_고정대기각_범위.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(report['counts']),flush=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--max-nfev',type=int,default=20)
    parser.add_argument('--budget-s',type=float,default=240.)
    args=parser.parse_args();run(args.out.resolve(),args.max_nfev,args.budget_s)
