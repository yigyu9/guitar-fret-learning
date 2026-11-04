"""T1/T2/T3의 압력 해제·팔 운반·다음 압현을 분리한 재생 요청각을 만든다.

기존 native 끝점 JSON만 읽으며 학습 입력·봉인 도구를 수정하지 않는다.
경유점은 reset이나 정답 주입이 아닌 별도 물리 대조의 목표각 요청이다.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
import numpy as np

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
STUDY = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def generate(out):
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.core.control import target_rates
    contract = load_gpu_prepared_reset_contract('left')
    names = contract['initial']['joint_names']
    lower = np.asarray(contract['initial']['native_PD_properties']['lower'])
    upper = np.asarray(contract['initial']['native_PD_properties']['upper'])
    rates = target_rates(names)
    rates[[i for i,name in enumerate(names) if name.startswith('LH:')]] = 4.
    common_pins = dict(contract['source_sha256'])
    for function in (load_gpu_prepared_reset_contract,target_rates):
        p = Path(inspect.getsourcefile(function)).resolve();common_pins[str(p)] = sha(p)
    common_pins[str(Path(__file__).resolve())] = sha(__file__)
    out = Path(out).resolve();out.relative_to(ROOT);out.mkdir(parents=True,exist_ok=False)
    results = {}
    for case in ('T1','T2','T3'):
        folder = STUDY/'입력'/case
        docs = {name:json.loads((folder/name).read_text()) for name in
            ('catalog.json','known_press.json','manifest.json','provenance.json')}
        manifest = docs['manifest.json']
        for filename,key in (('catalog.json','catalog_sha256'),('known_press.json','known_press_sha256'),
                             ('provenance.json','provenance_sha256')):
            if sha(folder/filename) != manifest[key]:raise ValueError('입력 manifest 불일치: '+case+'/'+filename)
        pins = dict(common_pins);pins.update(docs['provenance.json']['active_physical_inputs'])
        pins.update({str(folder/name):sha(folder/name) for name in docs})
        for name,expected in pins.items():
            if sha(name) != expected:raise ValueError('입력 SHA 불일치: '+name)
        catalog = docs['catalog.json'];row = catalog['goals'][0];known = docs['known_press.json']
        if row['case_id'] != case or len(known['events']) != 2 or row['control_scope'] != 'arm_and_goals':
            raise ValueError('T1/T2/T3 두 목표 전환 계약 필요')
        indices = np.array(catalog['action_indices'][:12]+[i for finger in row['target_fingers']
            for i in range(52+4*finger,56+4*finger)])
        action_lookup = {i:(lo,hi) for i,lo,hi in zip(catalog['action_indices'],catalog['action_lower'],catalog['action_upper'])}
        action_low = np.array([action_lookup[i][0] for i in indices])
        action_high = np.array([action_lookup[i][1] for i in indices])
        initial = np.asarray(row['q105'],dtype=float)
        if initial.shape != (105,) or not np.isfinite(initial).all():raise ValueError('유한 실측 q105 필요')
        endpoints = [known['endpoint_states'][event['endpoint_case']] for event in known['events']]
        def request(source):
            result = initial.copy();result[indices] = np.asarray(source,dtype=float)[indices]
            return result
        a_press = request(endpoints[0]['press_q105'])
        b_arrival = request(endpoints[1]['arrival_q105'])
        b_press = request(endpoints[1]['press_q105'])
        points = [(0.,initial),(.5,initial),(2.5,a_press),(4.5,a_press),
                  (4.6,initial),(5.3,b_arrival),(5.4,b_press),(7.,b_press),
                  (7.1,b_arrival),(7.5,b_arrival)]
        segments = []
        for (start,a),(end,b) in zip(points,points[1:]):
            requested = 1.875*np.abs(b[indices]-a[indices])/(end-start)
            ratio = requested/rates[indices]
            segments.append(dict(start_s=start,end_s=end,maximum_peak_rate_rad_s=float(requested.max()),
                maximum_peak_rate_ratio=float(ratio.max()),requested_rate_feasible=bool((ratio<=1.+1e-6).all())))
        finite = all(q.shape==(105,) and np.isfinite(q).all() for _,q in points)
        native = all(np.all(q[indices]>=lower[indices]-1e-6) and np.all(q[indices]<=upper[indices]+1e-6) for _,q in points)
        action = all(np.all(q[indices]>=action_low-1e-6) and np.all(q[indices]<=action_high+1e-6) for _,q in points)
        inactive = np.setdiff1d(np.arange(105),indices)
        if not all(np.array_equal(q[inactive],initial[inactive]) for _,q in points):raise ValueError('비담당 관절 요청 변경')
        valid = finite and native and action and all(r['requested_rate_feasible'] for r in segments)
        reference = dict(schema='guitar_learning.complex_press_reference.v1',case_id=case,
            catalog_sha256=sha(folder/'catalog.json'),source_sha256=pins,candidate_valid=bool(valid),
            native_verified=False,active_indices=indices.tolist(),
            waypoints=[dict(time_s=time,q105=q.tolist()) for time,q in points],segment_rates=segments,
            active_native_limits_valid=bool(native),active_controller_action_limits_valid=bool(action),
            inactive105_request_preserved=True,all105_initial_observed_min_native_margin_rad=float(np.minimum(initial-lower,upper-initial).min()),
            scope='recorded endpoint request angles; explicit A release then B arrival then B press; no state reset or policy teacher',
            limitation='CPU limits/rate/endpoint provenance only. Finger-path interference, physical contact release, moving guitar and timing require native replay')
        path = out/(case+'_reference.json');write(path,reference)
        results[case] = dict(path=str(path),sha256=sha(path),candidate_valid=bool(valid),
            active_axes=len(indices),maximum_peak_rate_ratio=max(s['maximum_peak_rate_ratio'] for s in segments),
            source_pins_verified=len(pins),native_verified=False)
    write(out/'CPU검증.json',dict(completed=True,results=results,
        generator_sha256=sha(__file__),native_verified=False,
        unchanged_source='기존 inputs.py/입력/geometry.py/reference v4는 읽기만 하거나 접근하지 않음'))
    return results


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=STUDY/'검증/복합기하/전환경로_v1')
    args = parser.parse_args();result = generate(args.out)
    print(json.dumps(dict(completed=True,results=result),ensure_ascii=False))
